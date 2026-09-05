
// ============================================================
// VIDEO ROOM - WEBRTC
// ============================================================

const roomId = window.chatConfig.roomId;
const currentUserId = window.chatConfig.currentUserId;

const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const cameraBtn = document.getElementById("cameraBtn");
const micBtn = document.getElementById("micBtn");

let localStream = new MediaStream();
let remoteStream = new MediaStream();

let peerConnection = null;
let videoSocket = null;

let pendingCandidates = [];

// let cameraOn = true;
// ============================================================
// START CAMERA
// ============================================================

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });

        localStream = stream;

        localVideo.srcObject = localStream;

        // Initial button state
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
        console.log("🎤 Local microphone started");

    } catch (error) {

        console.warn(
            "⚠️ Local camera unavailable:",
            error
        );

        // This can happen when another browser
        // is already using the physical camera.
        localStream = new MediaStream();

        localVideo.srcObject = null;

        console.log(
            "📷 Continuing without local camera"
        );

        // Disable buttons if there is no local stream
        cameraBtn.textContent = "🚫 Camera Off";
        micBtn.textContent = "🔇 Mic Off";
    }

    connectSignaling();
}


// ============================================================
// WEBSOCKET
// ============================================================

function connectSignaling() {

    const protocol =
        window.location.protocol === "https:"
            ? "wss:"
            : "ws:";

    const socketUrl =
        `${protocol}//${window.location.host}/ws/video/${roomId}/`;

    console.log(
        "🔌 Connecting video WebSocket:",
        socketUrl
    );

    videoSocket = new WebSocket(socketUrl);


    videoSocket.onopen = function () {

        console.log(
            "✅ Video WebSocket connected"
        );

    };


    videoSocket.onmessage = async function (event) {

        const data = JSON.parse(event.data);

        console.log(
            "📨 Video signal:",
            data
        );


        // ====================================================
        // USER JOINED
        // ====================================================

        

        if (data.type === "user_joined") {

            console.log(
                "👤 User joined:",
                data.username
            );

            const hasCamera =
                localStream &&
                localStream.getVideoTracks().length > 0;

            if (hasCamera) {

                console.log(
                    "📹 I have camera → creating offer"
                );

                await createOffer();

            } else {

                console.log(
                    "📷 No camera → waiting for offer"
                );
            }
        }


        // ====================================================
        // OFFER
        // ====================================================

        else if (data.type === "offer") {

            console.log(
                "📥 Offer received"
            );

            await handleOffer(data.offer);

        }


        // ====================================================
        // ANSWER
        // ====================================================

        else if (data.type === "answer") {

            console.log(
                "📥 Answer received"
            );

            await handleAnswer(data.answer);

        }


        // ====================================================
        // ICE
        // ====================================================

        else if (data.type === "ice_candidate") {

            await handleIceCandidate(
                data.candidate
            );

        }


        // ====================================================
        // USER LEFT
        // ====================================================

        else if (data.type === "user_left") {

            console.log(
                "👋 User left"
            );

            closePeerConnection();

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
// CREATE PEER CONNECTION
// ============================================================

function createPeerConnection() {

    if (peerConnection) {

        return peerConnection;

    }


    console.log(
        "🔗 Creating peer connection"
    );


    peerConnection = new RTCPeerConnection({

        iceServers: [
            {
                urls: "stun:stun.l.google.com:19302"
            }
        ]

    });


    // ========================================================
    // CREATE REMOTE STREAM
    // ========================================================

    remoteStream = new MediaStream();

    remoteVideo.srcObject = remoteStream;


    // ========================================================
    // ADD LOCAL TRACKS
    // ========================================================

    localStream.getTracks().forEach(function (track) {

        console.log(
            "➕ Adding local track:",
            track.kind
        );

        peerConnection.addTrack(
            track,
            localStream
        );

    });


    // ========================================================
    // REMOTE TRACK
    // ========================================================

    peerConnection.ontrack = function (event) {

        console.log(
            "🎥 Remote track received:",
            event.track.kind
        );


        /*
         * IMPORTANT:
         *
         * Don't replace remoteVideo.srcObject with
         * event.streams[0].
         *
         * Instead, add the received track to our own
         * remote MediaStream.
         */

        const alreadyExists =
            remoteStream
                .getTracks()
                .some(
                    track => track.id === event.track.id
                );


        if (!alreadyExists) {

            remoteStream.addTrack(
                event.track
            );

        }


        remoteVideo.srcObject = remoteStream;


        // Make sure the video is visible

        remoteVideo.autoplay = true;
        remoteVideo.playsInline = true;


        remoteVideo.play()
            .then(function () {

                console.log(
                    "▶️ Remote video playing"
                );

            })
            .catch(function (error) {

                console.log(
                    "⚠️ Remote video play:",
                    error
                );

            });


        console.log(
            "✅ Remote stream assigned"
        );

    };


    // ========================================================
    // ICE CANDIDATE
    // ========================================================

    peerConnection.onicecandidate = function (event) {

        if (
            event.candidate &&
            videoSocket &&
            videoSocket.readyState === WebSocket.OPEN
        ) {

            videoSocket.send(
                JSON.stringify({

                    type: "ice_candidate",

                    candidate: event.candidate

                })
            );

        }

    };


    // ========================================================
    // ICE CONNECTION
    // ========================================================

    peerConnection.oniceconnectionstatechange =
        function () {

            console.log(
                "🧊 ICE connection:",
                peerConnection.iceConnectionState
            );

        };


    // ========================================================
    // WEBRTC CONNECTION
    // ========================================================

    peerConnection.onconnectionstatechange =
        function () {

            console.log(
                "🔗 WebRTC connection:",
                peerConnection.connectionState
            );

        };


    return peerConnection;
}


// ============================================================
// CREATE OFFER
// ============================================================

async function createOffer() {

    try {

        const pc =
            createPeerConnection();


        console.log(
            "📤 Creating offer"
        );


        const offer =
            await pc.createOffer();


        await pc.setLocalDescription(
            offer
        );


        console.log(
            "📤 Sending offer"
        );


        videoSocket.send(
            JSON.stringify({

                type: "offer",

                offer: pc.localDescription

            })
        );

    } catch (error) {

        console.error(
            "❌ Create offer error:",
            error
        );

    }
}


// ============================================================
// HANDLE OFFER
// ============================================================

async function handleOffer(offer) {

    try {

        const pc =
            createPeerConnection();


        console.log(
            "📥 Setting remote offer"
        );


        await pc.setRemoteDescription(
            new RTCSessionDescription(offer)
        );


        // Add candidates that arrived early

        for (
            const candidate of pendingCandidates
        ) {

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


        pendingCandidates = [];


        // Create answer

        const answer =
            await pc.createAnswer();


        await pc.setLocalDescription(
            answer
        );


        videoSocket.send(
            JSON.stringify({

                type: "answer",

                answer: pc.localDescription

            })
        );


        console.log(
            "📤 Answer sent"
        );

    } catch (error) {

        console.error(
            "❌ Handle offer error:",
            error
        );

    }
}


// ============================================================
// HANDLE ANSWER
// ============================================================

async function handleAnswer(answer) {

    try {

        if (!peerConnection) {

            return;

        }


        await peerConnection.setRemoteDescription(
            new RTCSessionDescription(answer)
        );


        // Add candidates that arrived early

        for (
            const candidate of pendingCandidates
        ) {

            try {

                await peerConnection.addIceCandidate(
                    candidate
                );

            } catch (error) {

                console.warn(
                    "⚠️ ICE error:",
                    error
                );

            }

        }


        pendingCandidates = [];


        console.log(
            "✅ Answer applied"
        );

    } catch (error) {

        console.error(
            "❌ Handle answer error:",
            error
        );

    }
}


// ============================================================
// HANDLE ICE
// ============================================================

async function handleIceCandidate(candidate) {

    try {

        const iceCandidate =
            new RTCIceCandidate(candidate);


        if (
            !peerConnection ||
            !peerConnection.remoteDescription
        ) {

            pendingCandidates.push(
                iceCandidate
            );

            return;

        }


        await peerConnection.addIceCandidate(
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
// CLOSE CONNECTION
// ============================================================

function closePeerConnection() {

    if (peerConnection) {

        peerConnection.close();

        peerConnection = null;

    }


    remoteStream =
        new MediaStream();

    remoteVideo.srcObject =
        remoteStream;

}

// ============================================================
// CAMERA TOGGLE
// ============================================================
async function toggleCamera() {
    const videoTracks = localStream.getVideoTracks();

    // CAMERA OFF
    if (videoTracks.length > 0) {
        const track = videoTracks[0];
        track.stop();
        localStream.removeTrack(track);

        const sender =
            peerConnection &&
            peerConnection.getSenders().find(
                s => s.track && s.track.kind === "video"
            );

        if (sender) {
            await sender.replaceTrack(null);
        }

        localVideo.srcObject = null;

        cameraBtn.textContent = "🚫 Camera Off";   // <-- ADD THIS
        console.log("📷 Camera OFF");
        return;
    }

    // CAMERA ON
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const track = stream.getVideoTracks()[0];

        localStream.addTrack(track);
        localVideo.srcObject = localStream;

        const sender =
            peerConnection &&
            peerConnection.getSenders().find(
                s => s.track && s.track.kind === "video"
            );

        if (sender) {
            await sender.replaceTrack(track);
        } else if (peerConnection) {
            peerConnection.addTrack(track, localStream);
        }

        cameraBtn.textContent = "📹 Camera On";   // <-- ADD THIS
        console.log("📷 Camera ON");
    } catch (error) {
        console.error("❌ Camera error:", error);
    }
}

// ============================================================
// MICROPHONE TOGGLE
// ============================================================
async function toggleMicrophone() {
    const audioTracks = localStream.getAudioTracks();

    if (audioTracks.length > 0) {
        audioTracks[0].enabled = !audioTracks[0].enabled;

        micBtn.textContent = audioTracks[0].enabled   // <-- ADD THIS
            ? "🎤 Mic On"
            : "🔇 Mic Off";

        console.log(audioTracks[0].enabled ? "🎤 Microphone ON" : "🎤 Microphone OFF");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const track = stream.getAudioTracks()[0];

        localStream.addTrack(track);

        if (peerConnection) {
            peerConnection.addTrack(track, localStream);
        }

        micBtn.textContent = "🎤 Mic On";   // <-- ADD THIS
        console.log("🎤 Microphone ON");
    } catch (error) {
        console.error("❌ Microphone error:", error);
    }
}

// ============================================================
// START
// ============================================================

startCamera();