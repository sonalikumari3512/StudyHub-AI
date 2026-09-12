// ============================================================
// VIDEO ROOM - WEBRTC (MULTI-PEER)
// ============================================================

const roomId = window.chatConfig.roomId;
const currentUserId = window.chatConfig.currentUserId;
const currentUsername = window.chatConfig.currentUsername;

const videoGrid = document.getElementById("videoGrid");
const cameraBtn = document.getElementById("cameraBtn");
const micBtn = document.getElementById("micBtn");
const screenShareBtn = document.getElementById("screenShareBtn");

let screenStream = null;
let isScreenSharing = false;
let localStream = new MediaStream();
let videoSocket = null;

// Map<peerId, RTCPeerConnection>
const peerConnections = new Map();

// Map<peerId, MediaStream>
const remoteStreams = new Map();

// Map<peerId, { candidates: [] }>
// ICE candidates that arrive before remoteDescription is set
const pendingCandidates = new Map();

const toastContainer = document.getElementById("toastContainer");


// ============================================================
// TOAST
// ============================================================

function showParticipantToast(message, type = "joined") {
    const toast = document.createElement("div");

    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    if (toastContainer) {
        toastContainer.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add("show");
        });

        setTimeout(() => {
            toast.classList.remove("show");

            setTimeout(() => {
                toast.remove();
            }, 350);
        }, 3000);
    }
}


// ============================================================
// START CAMERA
// ============================================================

async function startCamera() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true,
        });

        addLocalVideoTile();

        const videoTrack = localStream.getVideoTracks()[0];
        const audioTrack = localStream.getAudioTracks()[0];

        if (videoTrack) {
            videoTrack.enabled = true;
            cameraBtn.textContent = "📹 Camera On";
        }

        if (audioTrack) {
            audioTrack.enabled = true;
            micBtn.textContent = "🎤 Mic On";
        }

        console.log("📹 Local camera started");

    } catch (error) {
        console.warn(
            "⚠️ Camera/mic unavailable, joining audio/video-less:",
            error
        );

        try {
            // Fall back to audio-only
            localStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });

        } catch (audioError) {
            console.warn(
                "⚠️ No audio either, joining with no media:",
                audioError
            );

            localStream = new MediaStream();
        }

        addLocalVideoTile();

        cameraBtn.textContent = "🚫 Camera Off";

        micBtn.textContent = localStream.getAudioTracks().length
            ? "🎤 Mic On"
            : "🔇 Mic Off";
    }

    connectSignaling();
}


// ============================================================
// VIDEO TILE HELPERS
// ============================================================

function addLocalVideoTile() {
    // Prevent duplicate local tile
    if (document.getElementById("tile-local")) {
        const existingVideo = document.getElementById("localVideo");

        if (existingVideo) {
            existingVideo.srcObject = localStream;
        }

        return;
    }

    const card = document.createElement("div");

    card.className = "video-card";
    card.id = "tile-local";

    const video = document.createElement("video");

    video.id = "localVideo";
    video.autoplay = true;
    video.playsInline = true;
    video.muted = true;

    video.srcObject = localStream;

    const label = document.createElement("div");

    label.className = "video-name";
    label.textContent = `You (${currentUsername})`;

    card.appendChild(video);
    card.appendChild(label);

    videoGrid.appendChild(card);
}


function addRemoteVideoTile(peerId, username) {
    if (document.getElementById(`tile-${peerId}`)) {
        return;
    }

    const card = document.createElement("div");

    card.className = "video-card";
    card.id = `tile-${peerId}`;

    const video = document.createElement("video");

    video.id = `video-${peerId}`;
    video.autoplay = true;
    video.playsInline = true;

    const label = document.createElement("div");

    label.className = "video-name";
    label.textContent = username || "Participant";

    card.appendChild(video);
    card.appendChild(label);

    videoGrid.appendChild(card);
}


function removeRemoteVideoTile(peerId) {
    const card = document.getElementById(`tile-${peerId}`);

    if (card) {
        card.remove();
    }
}


// ============================================================
// PRESENTATION MODE
// ============================================================

function enablePresentationMode(username) {
    // Add layout class to the grid
    videoGrid.classList.add("presentation-mode");

    // Remove old presenter class
    document.querySelectorAll(".video-card").forEach((card) => {
        card.classList.remove("presenting");
    });

    // Local presenter
    if (username === currentUsername) {
        document
            .getElementById("tile-local")
            ?.classList.add("presenting");

        return;
    }

    // Remote presenter
    document.querySelectorAll(".video-card").forEach((card) => {
        const name = card
            .querySelector(".video-name")
            ?.innerText
            .trim();

        if (name === username) {
            card.classList.add("presenting");
        }
    });
}


function disablePresentationMode() {
    videoGrid.classList.remove("presentation-mode");

    document.querySelectorAll(".video-card").forEach((card) => {
        card.classList.remove("presenting");
    });
}


// ============================================================
// WEBSOCKET
// ============================================================

function connectSignaling() {
    const protocol =
        window.location.protocol === "https:" ? "wss:" : "ws:";

    const socketUrl =
        `${protocol}//${window.location.host}/ws/video/${roomId}/`;

    console.log("🔌 Connecting video WebSocket:", socketUrl);

    videoSocket = new WebSocket(socketUrl);

    videoSocket.onopen = function () {
        console.log("✅ Video WebSocket connected");
    };


    videoSocket.onmessage = async function (event) {
        const data = JSON.parse(event.data);

        console.log("📨 Video signal:", data);

        switch (data.type) {

            // ==================================================
            // EXISTING ROOM USERS
            // ==================================================

            case "room_users":

                // Everyone already in the room
                for (const peer of data.users) {
                    addRemoteVideoTile(
                        peer.user_id,
                        peer.username
                    );

                    await createOfferTo(peer.user_id);
                }

                break;


            // ==================================================
            // WEBRTC OFFER
            // ==================================================

            case "offer":
                await handleOffer(
                    data.offer,
                    data.sender_id
                );

                break;


            // ==================================================
            // WEBRTC ANSWER
            // ==================================================

            case "answer":
                await handleAnswer(
                    data.answer,
                    data.sender_id
                );

                break;


            // ==================================================
            // ICE CANDIDATE
            // ==================================================

            case "ice_candidate":
                await handleIceCandidate(
                    data.candidate,
                    data.sender_id
                );

                break;


            // ==================================================
            // USER JOINED
            // ==================================================

            case "user_joined":

                console.log(
                    "👤 User joined:",
                    data.username
                );

                addRemoteVideoTile(
                    data.user_id,
                    data.username
                );

                showParticipantToast(
                    `🟢 ${data.username} joined the room`,
                    "joined"
                );

                break;


            // ==================================================
            // USER LEFT
            // ==================================================

            case "user_left":

                console.log(
                    "👋 User left:",
                    data.username
                );

                closePeerConnection(data.user_id);

                removeRemoteVideoTile(data.user_id);

                showParticipantToast(
                    `🔴 ${data.username} left the room`,
                    "left"
                );

                break;


            // ==================================================
            // SCREEN SHARE REQUEST APPROVED
            // ==================================================

            case "screen_share_allowed":

                console.log(
                    "✅ Screen sharing permission granted"
                );

                // IMPORTANT:
                // getDisplayMedia() is called ONLY here,
                // after server approval.
                await startApprovedScreenShare();

                break;


            // ==================================================
            // SCREEN SHARE REQUEST DENIED
            // ==================================================

            case "screen_share_denied":

                alert(
                    `🖥️ ${data.username} is already presenting.`
                );

                console.log(
                    `❌ Screen share denied. ${data.username} is already presenting.`
                );

                // IMPORTANT:
                // DO NOT call stopScreenSharing() here.
                //
                // We never started screen sharing because
                // the server rejected the request.

                break;


            // ==================================================
            // SCREEN SHARE STARTED
            // ==================================================

            case "screen_share_started": {

                const presentationBanner =
                    document.getElementById(
                        "presentationBanner"
                    );

                const presenterName =
                    document.getElementById(
                        "presenterName"
                    );

                if (presentationBanner) {
                    presentationBanner.style.display = "block";
                }

                if (presenterName) {
                    presenterName.innerText =
                        data.username;
                }

                enablePresentationMode(
                    data.username
                );

                showParticipantToast(
                    `🖥️ ${data.username} started presenting`,
                    "joined"
                );

                break;
            }


            // ==================================================
            // SCREEN SHARE STOPPED
            // ==================================================

            case "screen_share_stopped": {

                const presentationBanner =
                    document.getElementById(
                        "presentationBanner"
                    );

                if (presentationBanner) {
                    presentationBanner.style.display = "none";
                }

                disablePresentationMode();

                showParticipantToast(
                    `📹 ${data.username} stopped presenting`,
                    "left"
                );

                break;
            }
        }
    };


    videoSocket.onerror = function (error) {
        console.error(
            "❌ Video WebSocket error:",
            error
        );
    };


    videoSocket.onclose = function () {
        console.log(
            "🔌 Video WebSocket disconnected"
        );
    };
}


// ============================================================
// PEER CONNECTION (PER PEER)
// ============================================================

function getOrCreatePeerConnection(peerId) {

    if (peerConnections.has(peerId)) {
        return peerConnections.get(peerId);
    }

    console.log(
        "🔗 Creating peer connection for:",
        peerId
    );

    const pc = new RTCPeerConnection({
        iceServers: [
            {
                urls: "stun:stun.l.google.com:19302",
            },
        ],
    });

    remoteStreams.set(
        peerId,
        new MediaStream()
    );

    pendingCandidates.set(
        peerId,
        []
    );


    // --------------------------------------------------------
    // Add local tracks
    // --------------------------------------------------------

    localStream.getTracks().forEach((track) => {
        pc.addTrack(
            track,
            localStream
        );
    });


    // --------------------------------------------------------
    // Remote track
    // --------------------------------------------------------

    pc.ontrack = function (event) {

        console.log(
            "🎥 Remote track received from",
            peerId,
            ":",
            event.track.kind
        );

        const remoteStream =
            remoteStreams.get(peerId);

        const alreadyExists =
            remoteStream
                .getTracks()
                .some(
                    (t) =>
                        t.id === event.track.id
                );

        if (!alreadyExists) {
            remoteStream.addTrack(
                event.track
            );
        }

        const videoEl =
            document.getElementById(
                `video-${peerId}`
            );

        if (videoEl) {

            videoEl.srcObject =
                remoteStream;

            videoEl.onloadedmetadata =
                async () => {

                    try {
                        await videoEl.play();

                    } catch (err) {

                        console.error(
                            "❌ Remote video play failed:",
                            err
                        );
                    }
                };
        }
    };


    // --------------------------------------------------------
    // ICE candidate
    // --------------------------------------------------------

    pc.onicecandidate = function (event) {

        if (
            event.candidate &&
            videoSocket &&
            videoSocket.readyState === WebSocket.OPEN
        ) {

            videoSocket.send(
                JSON.stringify({
                    type: "ice_candidate",
                    candidate: event.candidate,
                    target_id: peerId,
                })
            );
        }
    };


    // --------------------------------------------------------
    // ICE connection state
    // --------------------------------------------------------

    pc.oniceconnectionstatechange = function () {

        console.log(
            `🧊 ICE connection [${peerId}]:`,
            pc.iceConnectionState
        );
    };


    // --------------------------------------------------------
    // Connection state
    // --------------------------------------------------------

    pc.onconnectionstatechange = function () {

        console.log(
            `🔗 WebRTC connection [${peerId}]:`,
            pc.connectionState
        );
    };


    peerConnections.set(
        peerId,
        pc
    );

    return pc;
}


// ============================================================
// REPLACE VIDEO TRACK FOR ALL PEERS
// ============================================================

function replaceVideoTrack(newTrack) {

    peerConnections.forEach(
        (pc, peerId) => {

            const sender =
                pc
                    .getSenders()
                    .find(
                        (sender) =>
                            sender.track &&
                            sender.track.kind === "video"
                    );

            if (sender) {

                sender
                    .replaceTrack(newTrack)
                    .then(() => {

                        console.log(
                            `🔄 Replaced video track for peer ${peerId}`
                        );

                    })
                    .catch((error) => {

                        console.error(
                            `❌ Failed to replace video track for peer ${peerId}:`,
                            error
                        );
                    });
            }
        }
    );
}


// ============================================================
// OFFER / ANSWER / ICE
// ============================================================

async function createOfferTo(peerId) {

    try {

        const pc =
            getOrCreatePeerConnection(peerId);

        const offer =
            await pc.createOffer();

        await pc.setLocalDescription(
            offer
        );

        videoSocket.send(
            JSON.stringify({
                type: "offer",
                offer: pc.localDescription,
                target_id: peerId,
            })
        );

        console.log(
            "📤 Offer sent to",
            peerId
        );

    } catch (error) {

        console.error(
            "❌ Create offer error:",
            error
        );
    }
}


async function handleOffer(
    offer,
    senderId
) {

    try {

        addRemoteVideoTile(senderId);

        const pc =
            getOrCreatePeerConnection(
                senderId
            );

        await pc.setRemoteDescription(
            new RTCSessionDescription(
                offer
            )
        );

        const queued =
            pendingCandidates.get(
                senderId
            ) || [];

        for (const candidate of queued) {

            try {

                await pc.addIceCandidate(
                    candidate
                );

            } catch (error) {

                console.warn(
                    "⚠️ Pending ICE error:",
                    error
                );
            }
        }

        pendingCandidates.set(
            senderId,
            []
        );

        const answer =
            await pc.createAnswer();

        await pc.setLocalDescription(
            answer
        );

        videoSocket.send(
            JSON.stringify({
                type: "answer",
                answer: pc.localDescription,
                target_id: senderId,
            })
        );

        console.log(
            "📤 Answer sent to",
            senderId
        );

    } catch (error) {

        console.error(
            "❌ Handle offer error:",
            error
        );
    }
}


async function handleAnswer(
    answer,
    senderId
) {

    try {

        const pc =
            peerConnections.get(
                senderId
            );

        if (!pc) {
            return;
        }

        await pc.setRemoteDescription(
            new RTCSessionDescription(
                answer
            )
        );

        const queued =
            pendingCandidates.get(
                senderId
            ) || [];

        for (const candidate of queued) {

            try {

                await pc.addIceCandidate(
                    candidate
                );

            } catch (error) {

                console.warn(
                    "⚠️ ICE error:",
                    error
                );
            }
        }

        pendingCandidates.set(
            senderId,
            []
        );

        console.log(
            "✅ Answer applied from",
            senderId
        );

    } catch (error) {

        console.error(
            "❌ Handle answer error:",
            error
        );
    }
}


async function handleIceCandidate(
    candidate,
    senderId
) {

    try {

        const iceCandidate =
            new RTCIceCandidate(
                candidate
            );

        const pc =
            peerConnections.get(
                senderId
            );

        if (
            !pc ||
            !pc.remoteDescription
        ) {

            const queue =
                pendingCandidates.get(
                    senderId
                ) || [];

            queue.push(
                iceCandidate
            );

            pendingCandidates.set(
                senderId,
                queue
            );

            return;
        }

        await pc.addIceCandidate(
            iceCandidate
        );

    } catch (error) {

        console.error(
            "❌ ICE candidate error:",
            error
        );
    }
}


// ============================================================
// CLOSE / CLEANUP
// ============================================================

function closePeerConnection(peerId) {

    const pc =
        peerConnections.get(
            peerId
        );

    if (pc) {

        pc.close();

        peerConnections.delete(
            peerId
        );
    }

    remoteStreams.delete(
        peerId
    );

    pendingCandidates.delete(
        peerId
    );
}


// ============================================================
// CAMERA / MIC TOGGLE
// ============================================================

function toggleCamera() {

    const videoTrack =
        localStream.getVideoTracks()[0];

    if (!videoTrack) {
        return;
    }

    videoTrack.enabled =
        !videoTrack.enabled;

    cameraBtn.textContent =
        videoTrack.enabled
            ? "📹 Camera On"
            : "🚫 Camera Off";

    console.log(
        "Camera:",
        videoTrack.enabled
            ? "ON"
            : "OFF"
    );
}


function toggleMicrophone() {

    const audioTrack =
        localStream.getAudioTracks()[0];

    if (!audioTrack) {
        return;
    }

    audioTrack.enabled =
        !audioTrack.enabled;

    micBtn.textContent =
        audioTrack.enabled
            ? "🎤 Mic On"
            : "🔇 Mic Off";

    console.log(
        "Mic:",
        audioTrack.enabled
            ? "ON"
            : "OFF"
    );
}


// ============================================================
// SCREEN SHARE - REQUEST PERMISSION
// ============================================================

async function toggleScreenShare() {

    try {

        // ----------------------------------------------------
        // STOP SHARING
        // ----------------------------------------------------

        if (isScreenSharing) {

            stopScreenSharing();

            return;
        }


        // ----------------------------------------------------
        // CHECK WEBSOCKET
        // ----------------------------------------------------

        if (
            !videoSocket ||
            videoSocket.readyState !== WebSocket.OPEN
        ) {

            console.error(
                "❌ Video WebSocket is not connected"
            );

            return;
        }


        // ----------------------------------------------------
        // ASK SERVER FOR PERMISSION
        // ----------------------------------------------------

        videoSocket.send(
            JSON.stringify({
                type: "screen_share_request",
            })
        );

        console.log(
            "📤 Screen share permission requested"
        );

    } catch (error) {

        console.error(
            "❌ Screen share request failed:",
            error
        );
    }
}


// ============================================================
// START APPROVED SCREEN SHARE
// ============================================================

async function startApprovedScreenShare() {

    // Prevent duplicate start
    if (isScreenSharing) {
        return;
    }

    try {

        // ----------------------------------------------------
        // START SCREEN CAPTURE
        //
        // IMPORTANT:
        // This function is ONLY called after the server
        // sends "screen_share_allowed".
        // ----------------------------------------------------

        screenStream =
            await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: false,
            });

        const screenTrack =
            screenStream.getVideoTracks()[0];

        if (!screenTrack) {

            console.error(
                "❌ No screen video track available"
            );

            screenStream = null;

            return;
        }


        // ----------------------------------------------------
        // SHOW SCREEN LOCALLY
        // ----------------------------------------------------

        const localVideo =
            document.getElementById(
                "localVideo"
            );

        if (localVideo) {

            localVideo.srcObject =
                screenStream;
        }


        // ----------------------------------------------------
        // REPLACE CAMERA VIDEO WITH SCREEN
        // ----------------------------------------------------

        replaceVideoTrack(
            screenTrack
        );


        // ----------------------------------------------------
        // TELL SERVER WE ACTUALLY STARTED
        // ----------------------------------------------------

        if (
            videoSocket &&
            videoSocket.readyState === WebSocket.OPEN
        ) {

            videoSocket.send(
                JSON.stringify({
                    type: "screen_share_started",
                    username: currentUsername,
                })
            );
        }


        // ----------------------------------------------------
        // UPDATE STATE
        // ----------------------------------------------------

        isScreenSharing = true;

        screenShareBtn.innerText =
            "🛑 Stop Sharing";

        console.log(
            "🖥️ Screen sharing started"
        );


        // ----------------------------------------------------
        // USER CLICKS BROWSER'S "STOP SHARING"
        // ----------------------------------------------------

        screenTrack.onended = () => {

            if (isScreenSharing) {
                stopScreenSharing();
            }
        };

    } catch (error) {

        // User cancelled the browser picker
        console.error(
            "❌ Screen share cancelled:",
            error
        );

        screenStream = null;
        isScreenSharing = false;

        screenShareBtn.innerText =
            "🖥️ Share Screen";
    }
}


// ============================================================
// STOP SCREEN SHARE
// ============================================================

function stopScreenSharing() {

    if (!screenStream) {
        return;
    }

    const cameraTrack =
        localStream.getVideoTracks()[0];


    // --------------------------------------------------------
    // Stop screen capture
    // --------------------------------------------------------

    screenStream
        .getTracks()
        .forEach((track) => {
            track.stop();
        });

    screenStream = null;


    // --------------------------------------------------------
    // Restore webcam locally
    // --------------------------------------------------------

    const localVideo =
        document.getElementById(
            "localVideo"
        );

    if (localVideo) {

        localVideo.srcObject =
            localStream;
    }


    // --------------------------------------------------------
    // Send webcam back to peers
    // --------------------------------------------------------

    if (cameraTrack) {

        replaceVideoTrack(
            cameraTrack
        );
    }


    // --------------------------------------------------------
    // Tell server that presentation stopped
    // --------------------------------------------------------

    if (
        videoSocket &&
        videoSocket.readyState === WebSocket.OPEN
    ) {

        videoSocket.send(
            JSON.stringify({
                type: "screen_share_stopped",
                username: currentUsername,
            })
        );
    }


    // --------------------------------------------------------
    // Update state
    // --------------------------------------------------------

    isScreenSharing = false;

    screenShareBtn.innerText =
        "🖥️ Share Screen";

    console.log(
        "📹 Camera restored"
    );
}


// ============================================================
// LEAVE MEETING
// ============================================================

function leaveMeeting() {

    // Stop screen sharing first
    if (screenStream) {

        screenStream
            .getTracks()
            .forEach((track) => {
                track.stop();
            });

        screenStream = null;
        isScreenSharing = false;
    }


    // Stop local camera/mic immediately
    // This turns off the camera light
    localStream
        .getTracks()
        .forEach((track) => {
            track.stop();
        });


    // Close every peer connection
    for (const peerId of peerConnections.keys()) {

        closePeerConnection(
            peerId
        );
    }


    // Close signaling socket
    if (videoSocket) {
        videoSocket.close();
    }


    // Go back to room
    window.location.href =
        window.chatConfig.roomDetailUrl;
}


// ============================================================
// BEFORE UNLOAD
// ============================================================

window.addEventListener(
    "beforeunload",
    () => {

        localStream
            .getTracks()
            .forEach((track) => {
                track.stop();
            });

        if (screenStream) {

            screenStream
                .getTracks()
                .forEach((track) => {
                    track.stop();
                });
        }

        for (const peerId of peerConnections.keys()) {

            closePeerConnection(
                peerId
            );
        }
    }
);


// ============================================================
// START
// ============================================================

startCamera();

