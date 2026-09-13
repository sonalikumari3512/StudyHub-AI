import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from math import ceil
from .models import Room, Attendance

# ============================================================
# Active video room tracking
#
# room_id -> {
#     user_id: {
#         "channel_name": ...,
#         "username": ...
#     }
# }
# ============================================================

active_rooms = {}


# ============================================================
# Screen sharing tracking
#
# room_id -> username currently presenting
# ============================================================

active_presenters = {}


class VideoConsumer(AsyncWebsocketConsumer):
    # ==========================================
    # ATTENDANCE HELPERS
    # ==========================================

    @sync_to_async
    def mark_join(self):
        room = Room.objects.get(id=self.room_id)

        Attendance.objects.create(
            room=room,
            student=self.user,
            joined_at=timezone.now(),
            is_present=True
        )



    @sync_to_async
    def mark_leave(self):
        attendance = Attendance.objects.filter(
            room_id=self.room_id,
            student=self.user,
            left_at__isnull=True
        ).order_by("-joined_at").first()

        if attendance:
            attendance.left_at = timezone.now()

            duration = attendance.left_at - attendance.joined_at

            # Round up to at least 1 minute if someone attended.
            attendance.duration_minutes = max(
                1,
                ceil(duration.total_seconds() / 60)
            )

            attendance.save()
    # ========================================================
    # CONNECT
    # ========================================================

    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.video_group_name = f"video_{self.room_id}"

        # ----------------------------------------------------
        # Reject unauthenticated users
        # ----------------------------------------------------

        if not self.user.is_authenticated:
            await self.close()
            return

        # ----------------------------------------------------
        # Join video group
        # ----------------------------------------------------

        await self.channel_layer.group_add(
            self.video_group_name,
            self.channel_name
        )

        await self.accept()
        # Attendance created here
        await self.mark_join()
        # ----------------------------------------------------
        # Get/create room
        # ----------------------------------------------------

        room = active_rooms.setdefault(
            self.room_id,
            {}
        )

        # ----------------------------------------------------
        # Send existing users to newly connected user
        # ----------------------------------------------------

        existing_users = [
            {
                "user_id": uid,
                "username": info["username"]
            }
            for uid, info in room.items()
            if uid != self.user.id
        ]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "room_users",
                    "users": existing_users,
                }
            )
        )

        # ----------------------------------------------------
        # Register current user
        # ----------------------------------------------------

        room[self.user.id] = {
            "channel_name": self.channel_name,
            "username": self.user.username,
        }

        # ----------------------------------------------------
        # Tell everyone else that a new user joined
        # ----------------------------------------------------

        await self.channel_layer.group_send(
            self.video_group_name,
            {
                "type": "user_joined",
                "user_id": self.user.id,
                "username": self.user.username,
            }
        )

    # ========================================================
    # DISCONNECT
    # ========================================================

    async def disconnect(self, close_code):

        # ----------------------------------------------------
        # Leave video group
        # ----------------------------------------------------

        await self.channel_layer.group_discard(
            self.video_group_name,
            self.channel_name
        )

        # Attendance updated here
        await self.mark_leave()
        # ----------------------------------------------------
        # Remove user from active room
        # ----------------------------------------------------

        room = active_rooms.get(
            self.room_id
        )

        if room and self.user.id in room:
            del room[self.user.id]

            if not room:
                del active_rooms[self.room_id]

        # ----------------------------------------------------
        # Release presenter lock if this user was presenting
        # ----------------------------------------------------

        if (
            active_presenters.get(self.room_id)
            == self.user.username
        ):
            del active_presenters[self.room_id]

            # Tell everyone that screen sharing stopped
            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "screen_share_stopped",
                    "username": self.user.username,
                }
            )

        # ----------------------------------------------------
        # Tell everyone that the user left
        # ----------------------------------------------------

        await self.channel_layer.group_send(
            self.video_group_name,
            {
                "type": "user_left",
                "user_id": self.user.id,
                "username": self.user.username,
            }
        )

    # ========================================================
    # RECEIVE
    # ========================================================

    async def receive(self, text_data):

        data = json.loads(text_data)
        event_type = data.get("type")

        # ====================================================
        # WEBRTC OFFER
        # ====================================================

        if event_type == "offer":

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "video_offer",
                    "offer": data.get("offer"),
                    "sender_id": self.user.id,
                    "target_id": data.get("target_id"),
                }
            )

        # ====================================================
        # WEBRTC ANSWER
        # ====================================================

        elif event_type == "answer":

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "video_answer",
                    "answer": data.get("answer"),
                    "sender_id": self.user.id,
                    "target_id": data.get("target_id"),
                }
            )

        # ====================================================
        # ICE CANDIDATE
        # ====================================================

        elif event_type == "ice_candidate":

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "ice_candidate",
                    "candidate": data.get("candidate"),
                    "sender_id": self.user.id,
                    "target_id": data.get("target_id"),
                }
            )

        # ====================================================
        # SCREEN SHARE REQUEST
        #
        # IMPORTANT:
        # The browser has NOT called getDisplayMedia() yet.
        #
        # We only check whether this user is allowed to present.
        # ====================================================

        elif event_type == "screen_share_request":

            # ------------------------------------------------
            # Someone else is already presenting
            # ------------------------------------------------

            if (
                self.room_id in active_presenters
                and active_presenters[self.room_id]
                != self.user.username
            ):

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "screen_share_denied",
                            "username": active_presenters[
                                self.room_id
                            ],
                        }
                    )
                )

                return

            # ------------------------------------------------
            # Nobody else is presenting.
            #
            # Tell this user they are allowed to open the
            # browser screen picker.
            # ------------------------------------------------

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "screen_share_allowed",
                    }
                )
            )

        # ====================================================
        # SCREEN SHARE ACTUALLY STARTED
        #
        # This event comes AFTER the browser successfully
        # obtains the screen stream.
        # ====================================================

        elif event_type == "screen_share_started":

            # ------------------------------------------------
            # Lock this room to this presenter
            # ------------------------------------------------

            active_presenters[
                self.room_id
            ] = self.user.username

            # ------------------------------------------------
            # Tell everyone that screen sharing started
            # ------------------------------------------------

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "screen_share_started",
                    "username": self.user.username,
                }
            )

        # ====================================================
        # SCREEN SHARE STOPPED
        # ====================================================

        elif event_type == "screen_share_stopped":

            # ------------------------------------------------
            # Only current presenter can release the lock
            # ------------------------------------------------

            if (
                active_presenters.get(self.room_id)
                == self.user.username
            ):
                del active_presenters[self.room_id]

            # ------------------------------------------------
            # Tell everyone that screen sharing stopped
            # ------------------------------------------------

            await self.channel_layer.group_send(
                self.video_group_name,
                {
                    "type": "screen_share_stopped",
                    "username": self.user.username,
                }
            )

    # ========================================================
    # USER JOINED
    # ========================================================

    async def user_joined(self, event):

        # Don't send event back to same user
        if event["user_id"] == self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )

    # ========================================================
    # USER LEFT
    # ========================================================

    async def user_left(self, event):

        # Don't send event back to same user
        if event["user_id"] == self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )

    # ========================================================
    # VIDEO OFFER
    # ========================================================

    async def video_offer(self, event):

        # Only target user receives the offer
        if event["target_id"] != self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "offer",
                    "offer": event["offer"],
                    "sender_id": event["sender_id"],
                }
            )
        )

    # ========================================================
    # VIDEO ANSWER
    # ========================================================

    async def video_answer(self, event):

        # Only target user receives the answer
        if event["target_id"] != self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "answer",
                    "answer": event["answer"],
                    "sender_id": event["sender_id"],
                }
            )
        )

    # ========================================================
    # ICE CANDIDATE
    # ========================================================

    async def ice_candidate(self, event):

        # Only target user receives the ICE candidate
        if event["target_id"] != self.user.id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "ice_candidate",
                    "candidate": event["candidate"],
                    "sender_id": event["sender_id"],
                }
            )
        )

    # ========================================================
    # SCREEN SHARE STARTED EVENT
    # ========================================================

    async def screen_share_started(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "screen_share_started",
                    "username": event["username"],
                }
            )
        )

    # ========================================================
    # SCREEN SHARE STOPPED EVENT
    # ========================================================

    async def screen_share_stopped(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "screen_share_stopped",
                    "username": event["username"],
                }
            )
        )

