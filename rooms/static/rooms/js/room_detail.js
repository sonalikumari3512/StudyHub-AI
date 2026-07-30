// =========================================
// CHAT CONFIG
// =========================================

const roomId = window.chatConfig.roomId;
const currentUserId = Number(window.chatConfig.currentUserId);
const username = window.chatConfig.username;


// =========================================
// DOM
// =========================================

const chatBox = document.getElementById("chat-box");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");

const typingStatus = document.getElementById("typing-status");
const onlineCount = document.getElementById("online-count");

const emojiButton = document.getElementById("emoji-button");
const emojiBox = document.getElementById("emoji-box");

const searchButton = document.getElementById("search-button");
const searchBox = document.getElementById("search-box");
const searchInput = document.getElementById("message-search");

let typingTimer = null;


// =========================================
// SOCKET
// =========================================

const wsProtocol =
window.location.protocol === "https:"
? "wss://"
: "ws://";

const socket = new WebSocket(

`${wsProtocol}${window.location.host}/ws/rooms/${roomId}/`

);


// =========================================
// SOCKET EVENTS
// =========================================

socket.onopen = function(){

    console.log("Connected");

    scrollBottom();

};

socket.onerror = function(error){

    console.error(error);

};

socket.onclose = function(){

    console.log("Disconnected");

};


// =========================================
// HELPERS
// =========================================

function scrollBottom(){

    if(chatBox){

        chatBox.scrollTop =
        chatBox.scrollHeight;

    }

}


function escapeHTML(text){

    const div =
    document.createElement("div");

    div.innerText = text;

    return div.innerHTML;

}


function removeEmptyChat(){

    const empty =
    document.getElementById("empty-chat");

    if(empty){

        empty.remove();

    }

}


// =========================================
// CREATE MESSAGE HTML
// =========================================

function createMessageHTML(data){

    const mine =
    Number(data.user_id) === currentUserId;

    return `

<div
id="message-${data.id}"
class="message-row ${mine ? "my-row":"other-row"}">

    <div
    class="message-bubble ${mine ? "my-message":"other-message"}">

        <div class="d-flex align-items-center mb-2">

            <div class="avatar">

                ${escapeHTML(data.username.charAt(0).toUpperCase())}

            </div>

            <div class="ms-2">

                <strong>

                    ${escapeHTML(data.username)}

                </strong>

                <br>

                <small class="text-muted">

                    ${data.time}

                </small>

            </div>

        </div>

        <div
        id="body-${data.id}"
        class="message-text">

            ${escapeHTML(data.message)}

        </div>

        ${
        mine ?

        `

        <div class="mt-3 d-flex gap-2">

            <button
            type="button"
            class="btn btn-warning btn-sm edit-btn"
            data-id="${data.id}">

                ✏ Edit

            </button>

            <button
            type="button"
            class="btn btn-danger btn-sm delete-btn"
            data-id="${data.id}">

                🗑 Delete

            </button>

        </div>

        <div
        id="receipt-${data.id}"
        class="receipt">

            ${
            data.read
            ? "✓✓ Read"
            : data.delivered
            ? "✓✓ Delivered"
            : "✓ Sent"
            }

        </div>

        `

        :

        ""

        }

    </div>

</div>

`;

}

// =========================================
// RECEIVE MESSAGE
// =========================================

socket.onmessage = function(event){

    const data = JSON.parse(event.data);

    // ==========================
    // NEW MESSAGE
    // ==========================

    if(data.type === "message"){

        removeEmptyChat();

        chatBox.insertAdjacentHTML(

            "beforeend",

            createMessageHTML(data)

        );

        scrollBottom();

        if(Number(data.user_id) !== currentUserId){

            socket.send(JSON.stringify({

                type:"delivered",

                message_id:data.id

            }));

        }

        return;

    }


    // ==========================
    // EDITED
    // ==========================

    if (data.type === "edited") {

    const body = document.getElementById("body-" + data.id);

    if (body) {
        body.innerText = data.message;
    }

    return;
}

    // ==========================
    // DELETED
    // ==========================

    if(data.type === "deleted"){

        const msg = document.getElementById(

            "message-" + data.id

        );

        if(msg){

            msg.remove();

        }

        return;

    }


    // ==========================
    // DELIVERED
    // ==========================

    if(data.type === "delivered"){

        const receipt = document.getElementById(

            "receipt-" + data.id

        );

        if(receipt){

            receipt.innerHTML = "✓✓ Delivered";

        }

        return;

    }


    // ==========================
    // READ
    // ==========================

    if(data.type === "read"){

        const receipt = document.getElementById(

            "receipt-" + data.id

        );

        if(receipt){

            receipt.innerHTML = "✓✓ Read";

        }

        return;

    }


    // ==========================
    // TYPING
    // ==========================

    if(data.type === "typing"){

        if(data.username !== username){

            typingStatus.textContent =

                data.typing

                ? `${data.username} is typing...`

                : "";

        }

        return;

    }


    // ==========================
    // PRESENCE
    // ==========================

    if(data.type === "presence"){

        const badge = document.getElementById(

            "status-" + data.user_id

        );

        if(!badge){

            return;

        }

        if(data.online){

            badge.className =

            "badge bg-success";

            badge.innerHTML =

            "🟢 Online";

        }

        else{

            badge.className =

            "badge bg-secondary";

            badge.innerHTML =

            `Last Seen<br><small>${data.last_seen}</small>`;

        }

        return;

    }


    // ==========================
    // ONLINE COUNT
    // ==========================

    if(data.type === "online_count"){

        if(onlineCount){

            onlineCount.textContent = data.count;

        }

        return;

    }

};


// =========================================
// SEND MESSAGE
// =========================================

chatForm.addEventListener("submit", function(e){

    e.preventDefault();

    const message = messageInput.value.trim();

    if(message === ""){

        return;

    }

    socket.send(JSON.stringify({

        type:"message",

        message:message

    }));

    messageInput.value = "";

    messageInput.focus();

});
// =========================================
// EDIT + DELETE
// =========================================


// =====================================
// EDIT MESSAGE (Simple & Reliable)
// =====================================

// =========================================
// EDIT + DELETE (Event Delegation)
// =========================================

chatBox.addEventListener("click", function (e) {
    // =====================================
    // EDIT MESSAGE
    // =====================================
    const editBtn = e.target.closest(".edit-btn");

    if (editBtn) {
        const id = editBtn.dataset.id;
        const body = document.getElementById("body-" + id);

        if (!body) return;

        const oldMessage = body.innerText.trim();
        const newMessage = prompt("Edit your message:", oldMessage);

        if (newMessage === null) {
            return; // User canceled prompt
        }

        if (newMessage.trim() === "") {
            alert("Message cannot be empty.");
            return;
        }

        if (newMessage.trim() === oldMessage) {
            return; // No change
        }

        socket.send(JSON.stringify({
            type: "edit",
            message_id: id,
            message: newMessage.trim()
        }));

        return;
    }

    // =====================================
    // DELETE MESSAGE
    // =====================================
    const deleteBtn = e.target.closest(".delete-btn");

    if (deleteBtn) {
        const id = deleteBtn.dataset.id;

        if (!confirm("Delete this message?")) {
            return;
        }

        socket.send(JSON.stringify({
            type: "delete",
            message_id: id
        }));
    }
});
// =========================================
// TYPING INDICATOR
// =========================================

messageInput.addEventListener("input", function () {

    const typing = this.value.trim().length > 0;

    socket.send(JSON.stringify({

        type: "typing",

        typing: typing

    }));

    clearTimeout(typingTimer);

    typingTimer = setTimeout(function () {

        socket.send(JSON.stringify({

            type: "typing",

            typing: false

        }));

    }, 1000);

});


// =========================================
// EMOJI PICKER
// =========================================

if (emojiButton) {

    emojiButton.addEventListener("click", function () {

        emojiBox.style.display =
        emojiBox.style.display === "block"
        ? "none"
        : "block";

    });

}

document.querySelectorAll(".emoji").forEach(function (emoji) {

    emoji.addEventListener("click", function () {

        messageInput.value += this.innerText;

        messageInput.focus();

    });

});


// =========================================
// SEARCH
// =========================================

if (searchButton) {

    searchButton.addEventListener("click", function () {

        if (
            searchBox.style.display === "" ||
            searchBox.style.display === "none"
        ) {

            searchBox.style.display = "block";

            searchInput.focus();

        }

        else {

            searchBox.style.display = "none";

            searchInput.value = "";

            document.querySelectorAll(".message-text").forEach(function (msg) {

                msg.classList.remove("highlight");

            });

        }

    });

}

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const keyword =
        this.value.toLowerCase();

        document.querySelectorAll(".message-text").forEach(function (msg) {

            msg.classList.remove("highlight");

            if (

                keyword !== "" &&

                msg.innerText.toLowerCase().includes(keyword)

            ) {

                msg.classList.add("highlight");

            }

        });

    });

}


// =========================================
// READ RECEIPTS
// =========================================

window.addEventListener("focus", function () {

    document.querySelectorAll("[id^='receipt-']").forEach(function (receipt) {

        const id =
        receipt.id.replace("receipt-", "");

        socket.send(JSON.stringify({

            type: "read",

            message_id: id

        }));

    });

});


// =========================================
// AUTO SCROLL
// =========================================

scrollBottom();


// =========================================
// CLOSE EMOJI
// =========================================

document.addEventListener("click", function (e) {

    if (

        emojiButton &&
        emojiBox &&
        !emojiBox.contains(e.target) &&
        e.target !== emojiButton

    ) {

        emojiBox.style.display = "none";

    }

});


// =========================================
// ENTER TO SEND
// =========================================

messageInput.addEventListener("keydown", function (e) {

    if (

        e.key === "Enter" &&

        !e.shiftKey

    ) {

        e.preventDefault();

        chatForm.dispatchEvent(

            new Event("submit")

        );

    }

});


// =========================================
// KEEP INPUT FOCUSED
// =========================================

if (messageInput) {

    messageInput.focus();

}


// =========================================
// CLOSE SOCKET
// =========================================

window.addEventListener("beforeunload", function () {

    if (

        socket.readyState === WebSocket.OPEN

    ) {

        socket.close();

    }

});