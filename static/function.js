// Constants for image paths
const botImagePath = "/static/chatbot_profile.jpg";
const userImagePath = "https://api.dicebear.com/8.x/initials/svg?seed=You&backgroundColor=00897b,00acc1,039be5,3949ab,43a047,5e35b1,6d4c41,7cb342,8e24aa,c0ca33,d81b60,e53935,f4511e,fb8c00,fdd835&backgroundType=gradientLinear&fontSize=40";

/**
 * Scrolls the message body to the bottom.
 */
function scrollToBottom() {
    var messageBody = document.getElementById("messageFormeight");
    messageBody.scrollTop = messageBody.scrollHeight;
}

/**
 * Gets the current time in HH:MM format.
 * @returns {string} The current time.
 */
function getCurrentTime() {
    const date = new Date();
    const hour = date.getHours().toString().padStart(2, '0');
    const minute = date.getMinutes().toString().padStart(2, '0');
    return hour + ":" + minute;
}

/**
 * Adds a message to the chat interface.
 * Handles Markdown rendering for bot messages and formats sources.
 * @param {string} message - The message content.
 * @param {boolean} isUser - True if the message is from the user, false if from the bot.
 * @param {Array<string>} [sources=[]] - An array of source strings (e.g., "filename.pdf, Page X.0").
 */
function addMessage(message, isUser = false, sources = []) {
    const time = getCurrentTime();
    let messageContentHtml; 
    
    if (isUser) {
        messageContentHtml = message; 
    } else {
        // Render Markdown content for bot messages
        messageContentHtml = marked.parse(message); 

        // Format and append sources if available
        if (sources && sources.length > 0) {
            const groupedSources = {};
            sources.forEach(source => {
                const parts = source.split(', Page ');
                const filename = parts[0];
                const page = parts[1];
                if (!groupedSources[filename]) {
                    groupedSources[filename] = [];
                }
                groupedSources[filename].push(page);
            });

            let formattedSourceStrings = [];
            for (const filename in groupedSources) {
                // Sort pages numerically
                const pages = groupedSources[filename].sort((a, b) => parseFloat(a) - parseFloat(b)); 
                formattedSourceStrings.push(`${filename}: Page ${pages.join(", Page ")}`);
            }
            
            messageContentHtml += `<div class="sources-info">Sources: ${formattedSourceStrings.join("; ")}</div>`;
        }
    }

    let messageHtml;
    if (isUser) {
        messageHtml = `
            <div class="d-flex justify-content-end mb-4">
                <div class="msg_cotainer_send">
                    ${messageContentHtml}
                    <span class="msg_time_send">${time}</span>
                </div>
                <div class="img_cont_msg">
                    <img src="${userImagePath}" class="rounded-circle user_img_msg" 
                         onerror="this.src='https://via.placeholder.com/40/00ACC1/FFFFFF?Text=U'">
                </div>
            </div>`;
    } else {
        messageHtml = `
            <div class="d-flex justify-content-start mb-4">
                <div class="img_cont_msg">
                    <img src="${botImagePath}" class="rounded-circle user_img_msg" 
                         onerror="this.src='https://via.placeholder.com/40/4A54E2/FFFFFF?Text=B'">
                </div>
                <div class="msg_cotainer">
                    ${messageContentHtml}
                    <span class="msg_time">${time}</span>
                </div>
            </div>`;
    }
    
    $("#messageFormeight").append(messageHtml);
    scrollToBottom();
}

/**
 * Displays a typing indicator for the bot.
 */
function showTypingIndicator() {
    const typingHtml = `
        <div id="typing-indicator" class="d-flex justify-content-start mb-4">
            <div class="img_cont_msg">
                <img src="${botImagePath}" class="rounded-circle user_img_msg" 
                     onerror="this.src='https://via.placeholder.com/40/4A54E2/FFFFFF?Text=B'">
            </div>
            <div class="msg_cotainer">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>`;
    $("#messageFormeight").append(typingHtml);
    scrollToBottom();
}

/**
 * Hides the typing indicator.
 */
function hideTypingIndicator() {
    $("#typing-indicator").remove();
}

// Document Ready Function - Initializes the chat interface
$(document).ready(function () {
    scrollToBottom();
    $("#text").focus();

    $("#messageArea").on("submit", function (event) {
        event.preventDefault();
        
        // Prevent multiple submissions while a request is pending
        if ($("#send").prop("disabled")) return;
        
        const rawText = $("#text").val().trim();
        if (!rawText) return;

        // Disable input and show loading state
        $("#text").prop("disabled", true).val("");
        $("#send").prop("disabled", true);
        $("#send i").removeClass("fa-paper-plane").addClass("fa-spinner fa-spin");

        // Add user message to chat
        addMessage(rawText, true);
        
        // Show typing indicator
        showTypingIndicator();

        // Send request to backend via AJAX
        $.ajax({
            url: "/chat",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                question: rawText,
                chat_history: [] // You might want to implement chat history logic here later
            }),
            timeout: 30000, // 30 second timeout for the request
            success: function(data) {
                hideTypingIndicator();
                addMessage(data.answer, false, data.sources);
            },
            error: function(xhr, status, error) {
                hideTypingIndicator();
                let errorMessage = "Sorry, I'm having trouble processing your request right now. Please try again later.";
                
                // Try to get a more specific error message from the backend if available
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    errorMessage = xhr.responseJSON.detail;
                } else if (status === "timeout") {
                    errorMessage = "Request timed out. The model might be loading. Please try again.";
                }
                
                addMessage(errorMessage, false);
            },
            complete: function() {
                // Re-enable input fields after request is complete (success or error)
                $("#text").prop("disabled", false);
                $("#send").prop("disabled", false);
                $("#send i").removeClass("fa-spinner fa-spin").addClass("fa-paper-plane");
                $("#text").focus(); // Return focus to the input field
            }
        });
    });
});