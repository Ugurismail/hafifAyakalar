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
                messageIcon.classList.add('text-danger');
            } else {
                messageIcon.classList.remove('text-danger');
            }
        });
    }

    // Her 30 saniyede bir yeni mesajları kontrol et
    setInterval(checkNewMessages, 30000);
});
