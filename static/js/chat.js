// static/js/chat.js

// CSRF Token'ı meta etiketinden al

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // İstediğimiz isimle başlayan bir çerez var mı kontrol edin
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrfToken = getCookie('csrftoken');

// Tüm AJAX isteklerine CSRF token'ını ekleyin
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^GET|HEAD|OPTIONS|TRACE$/.test(settings.type)) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        }
    }
});


// Global değişkenler
var openChats = {};  // Açık sohbetleri tutar
var newMessageCounts = {};  // Her bir kullanıcı için okunmamış mesaj sayısı
var notificationInterval;

// Sohbet penceresini açma fonksiyonu
function openChat(username, userId) {
    if (openChats[username]) {
        // Sohbet zaten açıksa, pencereyi göster ve öne getir
        openChats[username].window.show();
        bringChatToFront(username);
        return;
    }

    // Eğer userId tanımlı değilse, AJAX isteğiyle alalım
    if (!userId) {
        $.get('/users/get_user_id/' + username + '/', function(data) {
            userId = data.user_id;
            proceedToOpenChat(username, userId);
        });
    } else {
        proceedToOpenChat(username, userId);
    }
}

function proceedToOpenChat(username, userId) {
    var chatWindow = createChatWindow(username);
    $('body').append(chatWindow);
    openChats[username] = {
        userId: userId,
        window: chatWindow,
        isMinimized: true // Başlangıçta minimize edilmiş halde
    };

    positionChatWindows();
    loadMessages(username);
    bringChatToFront(username);

    // Açık sohbetleri localStorage'da güncelleyin
    var openChatUsers = Object.keys(openChats);
    localStorage.setItem('openChatUsers', JSON.stringify(openChatUsers));
}

// Sohbet penceresi oluşturma fonksiyonu
function createChatWindow(username) {
    // Sohbet penceresi HTML yapısını oluşturun
    var chatWindow = $('<div>').addClass('chat-window').attr('data-username', username);

    var chatHeader = $('<div>').addClass('chat-header');
    var title = $('<span>').text(username);
    var closeButton = $('<button>').addClass('close-button').text('X').click(function(event) {
        event.stopPropagation(); // Başlık tıklama olayını tetiklemesini engelle
        closeChat(username);
    });
    chatHeader.append(title).append(closeButton);

    var chatMessages = $('<div>').addClass('chat-messages');
    var chatInput = $('<div>').addClass('chat-input');
    var chatMessage = $('<textarea>').attr('rows', 2);
    var chatSend = $('<button>').text('Gönder').click(function() {
        sendMessage(username);
    });

    chatMessage.keypress(function(e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            sendMessage(username);
        }
    });

    chatInput.append(chatMessage).append(chatSend);

    chatWindow.append(chatHeader).append(chatMessages).append(chatInput);

    // Başlığa tıklama olayı ile minimize/maximize
    chatHeader.click(function(event) {
        // Eğer tıklanan eleman kapatma butonu değilse
        if (!$(event.target).hasClass('close-button')) {
            if (openChats[username].isMinimized) {
                restoreChat(username);
            } else {
                minimizeChat(username);
            }
        }
    });

    return chatWindow;
}

// Sohbet penceresini kapatma fonksiyonu
function closeChat(username) {
    if (openChats[username]) {
        openChats[username].window.remove();
        delete openChats[username];
        positionChatWindows();

        // Açık sohbetleri localStorage'da güncelleyin
        var openChatUsers = Object.keys(openChats);
        localStorage.setItem('openChatUsers', JSON.stringify(openChatUsers));
    }
}

// Sohbet penceresini minimize etme fonksiyonu
function minimizeChat(username) {
    var chat = openChats[username];
    var chatWindow = chat.window;
    chatWindow.removeClass('maximized'); // Maximize sınıfını kaldır
    chat.isMinimized = true;
    positionChatWindows();
}

// Sohbet penceresini maximize etme fonksiyonu
function restoreChat(username) {
    var chat = openChats[username];
    var chatWindow = chat.window;
    chatWindow.addClass('maximized'); // Maximize sınıfını ekle
    chat.isMinimized = false;
    positionChatWindows();
    chatWindow.find('.chat-messages').scrollTop(chatWindow.find('.chat-messages')[0].scrollHeight);
}

// Sohbet pencerelerinin konumunu ve genişliğini ayarlama fonksiyonu
function positionChatWindows() {
    var chatCount = Object.keys(openChats).length;
    if (chatCount === 0) return;

    var windowWidth = $(window).width();
    var chatWidth = Math.min(300, Math.floor((windowWidth - 20) / chatCount)); // Minimum 300px, aralarında 10px boşluk
    var index = 0;

    for (var username in openChats) {
        var chat = openChats[username];
        var chatWindow = chat.window;

        chatWindow.css({
            bottom: '0px',
            left: (index * (chatWidth + 10)) + 'px',
            width: chatWidth + 'px'
        });

        // Z-index ayarı
        chatWindow.css('z-index', 1000 + index);

        index++;
    }
}

// Sohbet penceresini öne getirme fonksiyonu
function bringChatToFront(username) {
    var chat = openChats[username];
    var chatWindow = chat.window;

    // Z-index değerini en yüksek yap
    var maxZIndex = 1000 + Object.keys(openChats).length;
    chatWindow.css('z-index', maxZIndex);
}

// Mesajları yükleme fonksiyonu
function loadMessages(username) {
    var chatWindow = openChats[username].window;
    var chatMessages = chatWindow.find('.chat-messages');

    $.get('/messages/get_conversation/' + username + '/', function(data) {
        chatMessages.empty();
        data.messages.forEach(function(message) {
            var messageElement = $('<div>').addClass('message');
            var senderSpan = $('<strong>').text(message.sender + ': ');
            var bodySpan = $('<span>').text(message.body);
            var timeSpan = $('<small>').text(' (' + message.timestamp + ')');
            messageElement.append(senderSpan).append(bodySpan).append(timeSpan);

            if (message.sender === username) {
                messageElement.addClass('recipient');
            } else {
                messageElement.addClass('sender');
            }
            chatMessages.append(messageElement);
        });
        chatMessages.scrollTop(chatMessages[0].scrollHeight);

        // Mesajlar yüklendiğinde okunmamış mesaj sayısını sıfırla ve stilini güncelle
        newMessageCounts[username] = 0;
        updateChatWindowStyle(username);
    });
}

// Mesaj gönderme fonksiyonu
function sendMessage(username) {
    var chatWindow = openChats[username].window;
    var chatMessage = chatWindow.find('textarea');
    var messageBody = chatMessage.val();
    if (messageBody.trim() === '') return;

    $.post('/messages/send_ajax/', {
        recipient_username: username,
        body: messageBody
    }, function(data) {
        var chatMessages = chatWindow.find('.chat-messages');
        var messageElement = $('<div>').addClass('message sender');
        var senderSpan = $('<strong>').text(data.sender + ': ');
        var bodySpan = $('<span>').text(data.body);
        var timeSpan = $('<small>').text(' (' + data.timestamp + ')');
        messageElement.append(senderSpan).append(bodySpan).append(timeSpan);

        chatMessages.append(messageElement);
        chatMessages.scrollTop(chatMessages[0].scrollHeight);
        chatMessage.val('');
    });
}

// Yeni mesajları kontrol etme fonksiyonu
function checkForNewMessages() {
    $.get('/messages/check_new_messages/', function(data) {
        if (data.new_messages && data.new_messages.length > 0) {
            data.new_messages.forEach(function(message) {
                var sender = message.sender;

                // Okunmamış mesaj sayısını artır
                if (newMessageCounts[sender]) {
                    newMessageCounts[sender]++;
                } else {
                    newMessageCounts[sender] = 1;
                }

                // Eğer sohbet penceresi açık değilse, açalım
                if (!openChats[sender]) {
                    openChat(sender, message.sender_id);
                } else {
                    // Sohbet penceresi açık ise, mesajları güncelle ve arka plan rengini değiştir
                    loadMessages(sender);
                    updateChatWindowStyle(sender);
                }

                updateUnreadCount();
            });
        }
    });
}

// Sohbet penceresinin stilini güncelleme fonksiyonu
function updateChatWindowStyle(username) {
    var chatWindow = openChats[username].window;
    if (newMessageCounts[username] && newMessageCounts[username] > 0) {
        // Okunmamış mesaj varsa arka plan rengini değiştir
        chatWindow.addClass('unread');
    } else {
        // Okunmamış mesaj yoksa arka plan rengini kaldır
        chatWindow.removeClass('unread');
    }
}

// Okunmamış mesaj sayısını güncelleme fonksiyonu
function updateUnreadCount() {
    var totalUnread = Object.values(newMessageCounts).reduce((a, b) => a + b, 0);
    var unreadCountElement = $('#unread-count');
    if (totalUnread > 0) {
        unreadCountElement.text('(' + totalUnread + ')');
    } else {
        unreadCountElement.text('');
    }
}

$(document).ready(function() {
    // "Mesaj Gönder" butonuna tıklama event'ı
    $(document).on('click', '.message-button', function() {
        var username = $(this).data('username');
        var userId = $(this).data('userid');
        openChat(username, userId);
    });

    // Yeni mesajları kontrol etmeyi başlat
    notificationInterval = setInterval(checkForNewMessages, 5000);

    // Tarayıcı bildirim iznini iste (isteğe bağlı)
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }

    // Sayfa yüklendiğinde okunmamış mesaj sayısını güncelle
    updateUnreadCount();

    // Sayfa yüklendiğinde açık sohbetleri geri yükleyin
    var openChatUsers = JSON.parse(localStorage.getItem('openChatUsers'));
    if (openChatUsers && openChatUsers.length > 0) {
        openChatUsers.forEach(function(username) {
            // Kullanıcının ID'sini almak için AJAX isteği yapabiliriz
            $.get('/users/get_user_id/' + username + '/', function(data) {
                var userId = data.user_id;
                openChat(username, userId);
            });
        });
    }

    // Pencere boyutu değiştiğinde sohbet pencerelerinin konumunu güncelle
    $(window).resize(function() {
        positionChatWindows();
    });
});

