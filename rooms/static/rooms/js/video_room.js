
/// ============================================================
// VIDEO ROOM - WEBRTC (MULTI-PEER)
// ============================================================

const roomId = window.chatConfig.roomId;
const currentUserId = window.chatConfig.currentUserId;
const currentUsername = window.chatConfig.currentUsername;

const videoGrid = document.getElementById("videoGrid");
const cameraBtn = document.getElementById("cameraBtn");
const micBtn = document.getElementById("micBtn");

let localStream = new MediaStream();
let videoSocket = null;

// Map<peerId, RTCPeerConnection>
const peerConnections = new Map();

// Map<peerId, MediaStream>
const remoteStreams = new Map();

// Map<peerId, { candidates: [] }>  -- ICE candidates that arrive before remoteDescription is set
const pendingCandidates = new Map();


// ============================================================
// START CAMERA
// ============================================================

async function startCamera() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
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
        console.warn("⚠️ Camera/mic unavailable, joining audio/video-less:", error);

        try {
            // Fall back to audio-only so the user can still join
            localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (audioError) {
            console.warn("⚠️ No audio either, joining with no media:", audioError);
            localStream = new MediaStream();
        }

        addLocalVideoTile();
        cameraBtn.textContent = "🚫 Camera Off";
        micBtn.textContent = localStream.getAudioTracks().length ? "🎤 Mic On" : "🔇 Mic Off";
    }

    connectSignaling();
}


// ============================================================
// VIDEO TILE HELPERS
// ============================================================

function addLocalVideoTile() {
    const card = document.createElement("div");
    card.className = "video-card";
    card.id = "tile-local";

    const video = document.createElement("video");
    video.id = "localVideo";
    video.autoplay = true;
    video.playsInline = true;
    video.muted = true; // never play back your own audio
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
        return; // already exists
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
// WEBSOCKET
// ============================================================

function connectSignaling() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socketUrl = `${protocol}//${window.location.host}/ws/video/${roomId}/`;

    console.log("🔌 Connecting video WebSocket:", socketUrl);

    videoSocket = new WebSocket(socketUrl);

    videoSocket.onopen = function () {
        console.log("✅ Video WebSocket connected");
    };

    videoSocket.onmessage = async function (event) {
        const data = JSON.parse(event.data);
        console.log("📨 Video signal:", data);

        switch (data.type) {

            case "room_users":
                // Roster of everyone already in the room.
                // We initiate offers to each of them.
                for (const peer of data.users) {
                    addRemoteVideoTile(peer.user_id, peer.username);
                    await createOfferTo(peer.user_id);
                }
                break;

            case "user_joined":
                console.log("👤 User joined:", data.username);
                addRemoteVideoTile(data.user_id, data.username);
                // We DON'T create an offer here — the new joiner
                // will send us one (they got our ID via room_users).
                break;

            case "offer":
                await handleOffer(data.offer, data.sender_id);
                break;

            case "answer":
                await handleAnswer(data.answer, data.sender_id);
                break;

            case "ice_candidate":
                await handleIceCandidate(data.candidate, data.sender_id);
                break;

            case "user_left":
                console.log("👋 User left:", data.username);
                closePeerConnection(data.user_id);
                removeRemoteVideoTile(data.user_id);
                break;
        }
    };

    videoSocket.onerror = function (error) {
        console.error("❌ Video WebSocket error:", error);
    };

    videoSocket.onclose = function () {
        console.log("🔌 Video WebSocket disconnected");
    };
}


// ============================================================
// PEER CONNECTION (per peer)
// ============================================================

function getOrCreatePeerConnection(peerId) {
    if (peerConnections.has(peerId)) {
        return peerConnections.get(peerId);
    }

    console.log("🔗 Creating peer connection for:", peerId);

    const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    });

    remoteStreams.set(peerId, new MediaStream());
    pendingCandidates.set(peerId, []);

    // Add our local tracks
    localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream);
    });

    pc.ontrack = function (event) {
        console.log("🎥 Remote track received from", peerId, ":", event.track.kind);

        const remoteStream = remoteStreams.get(peerId);

        const alreadyExists = remoteStream.getTracks().some(
            t => t.id === event.track.id
        );

        if (!alreadyExists) {
            remoteStream.addTrack(event.track);
        }

        const videoEl = document.getElementById(`video-${peerId}`);
        if (videoEl) {
            videoEl.srcObject = remoteStream;
            videoEl.onloadedmetadata = async () => {
                try {
                    await videoEl.play();
                } catch (err) {
                    console.error("❌ Remote video play failed:", err);
                }
            };
        }
    };

    pc.onicecandidate = function (event) {
        if (event.candidate && videoSocket && videoSocket.readyState === WebSocket.OPEN) {
            videoSocket.send(JSON.stringify({
                type: "ice_candidate",
                candidate: event.candidate,
                target_id: peerId,
            }));
        }
    };

    pc.oniceconnectionstatechange = function () {
        console.log(`🧊 ICE connection [${peerId}]:`, pc.iceConnectionState);
    };

    pc.onconnectionstatechange = function () {
        console.log(`🔗 WebRTC connection [${peerId}]:`, pc.connectionState);
    };

    peerConnections.set(peerId, pc);
    return pc;
}


// ============================================================
// OFFER / ANSWER / ICE
// ============================================================

async function createOfferTo(peerId) {
    try {
        const pc = getOrCreatePeerConnection(peerId);

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        videoSocket.send(JSON.stringify({
            type: "offer",
            offer: pc.localDescription,
            target_id: peerId,
        }));

        console.log("📤 Offer sent to", peerId);

    } catch (error) {
        console.error("❌ Create offer error:", error);
    }
}

async function handleOffer(offer, senderId) {
    try {
        addRemoteVideoTile(senderId); // ensure tile exists even if user_joined hasn't arrived yet
        const pc = getOrCreatePeerConnection(senderId);

        await pc.setRemoteDescription(new RTCSessionDescription(offer));

        const queued = pendingCandidates.get(senderId) || [];
        for (const candidate of queued) {
            try {
                await pc.addIceCandidate(candidate);
            } catch (error) {
                console.warn("⚠️ Pending ICE error:", error);
            }
        }
        pendingCandidates.set(senderId, []);

        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        videoSocket.send(JSON.stringify({
            type: "answer",
            answer: pc.localDescription,
            target_id: senderId,
        }));

        console.log("📤 Answer sent to", senderId);

    } catch (error) {
        console.error("❌ Handle offer error:", error);
    }
}

async function handleAnswer(answer, senderId) {
    try {
        const pc = peerConnections.get(senderId);
        if (!pc) return;

        await pc.setRemoteDescription(new RTCSessionDescription(answer));

        const queued = pendingCandidates.get(senderId) || [];
        for (const candidate of queued) {
            try {
                await pc.addIceCandidate(candidate);
            } catch (error) {
                console.warn("⚠️ ICE error:", error);
            }
        }
        pendingCandidates.set(senderId, []);

        console.log("✅ Answer applied from", senderId);

    } catch (error) {
        console.error("❌ Handle answer error:", error);
    }
}

async function handleIceCandidate(candidate, senderId) {
    try {
        const iceCandidate = new RTCIceCandidate(candidate);
        const pc = peerConnections.get(senderId);

        if (!pc || !pc.remoteDescription) {
            const queue = pendingCandidates.get(senderId) || [];
            queue.push(iceCandidate);
            pendingCandidates.set(senderId, queue);
            return;
        }

        await pc.addIceCandidate(iceCandidate);

    } catch (error) {
        console.error("❌ ICE candidate error:", error);
    }
}


// ============================================================
// CLOSE / CLEANUP
// ============================================================

function closePeerConnection(peerId) {
    const pc = peerConnections.get(peerId);
    if (pc) {
        pc.close();
        peerConnections.delete(peerId);
    }
    remoteStreams.delete(peerId);
    pendingCandidates.delete(peerId);
}


// ============================================================
// CAMERA / MIC TOGGLE
// ============================================================

function toggleCamera() {
    const videoTrack = localStream.getVideoTracks()[0];
    if (!videoTrack) return;

    videoTrack.enabled = !videoTrack.enabled;
    cameraBtn.textContent = videoTrack.enabled ? "📹 Camera On" : "🚫 Camera Off";
    console.log("Camera:", videoTrack.enabled ? "ON" : "OFF");
}

function toggleMicrophone() {
    const audioTrack = localStream.getAudioTracks()[0];
    if (!audioTrack) return;

    audioTrack.enabled = !audioTrack.enabled;
    micBtn.textContent = audioTrack.enabled ? "🎤 Mic On" : "🔇 Mic Off";
    console.log("Mic:", audioTrack.enabled ? "ON" : "OFF");
}


// ============================================================
// LEAVE MEETING
// ============================================================

function leaveMeeting() {
    // Stop local camera/mic immediately (turns off camera light)
    localStream.getTracks().forEach(track => track.stop());

    // Close every peer connection cleanly
    for (const peerId of peerConnections.keys()) {
        closePeerConnection(peerId);
    }

    // Close the signaling socket
    if (videoSocket) {
        videoSocket.close();
    }

    window.location.href = window.chatConfig.roomDetailUrl;
}

window.addEventListener("beforeunload", () => {
    localStream.getTracks().forEach(track => track.stop());
    for (const peerId of peerConnections.keys()) {
        closePeerConnection(peerId);
    }
});

// ============================================================
// START
// ============================================================

startCamera();