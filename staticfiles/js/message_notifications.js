// static/js/message_notifications.js

document.addEventListener('DOMContentLoaded', function() {
    function checkNewMessages() {
        fetch('/check_new_messages/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
        })
        .then(response => response.json())
        .then(data => {
            var messageIcon = document.getElementById('message-icon');
            if (data.unread_count > 0) {
                messageIcon.classList.add('msg');
            } else {
                messageIcon.classList.remove('msg');
            }
        });
    }

    // Her 30 saniyede bir yeni mesajları kontrol et
    setInterval(checkNewMessages, 30000);
});
