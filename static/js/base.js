/* base.js */

/**
 * CSRF Token alma fonksiyonu (eski kodunuzdan)
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        // Eğer cookie 'name=' ile başlıyorsa
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
}

/**
 * Arama özelliğini tek bir dosyada toplayan kod
 */
document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var searchResults = document.getElementById('search-results');

    var query = '';
    // Ok tuşları ile hangi öğe seçili olduğunu tutmak için:
    var currentFocus = -1;  

    searchInput.addEventListener('input', function() {
        query = this.value;
        if (query.length > 0) {
            fetch('/search/?q=' + encodeURIComponent(query), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Önceki sonuçları temizle
                searchResults.innerHTML = '';
                if (data.results.length > 0) {
                    data.results.forEach(function(item) {
                        var div = document.createElement('div');
                        div.classList.add('list-group-item');
                        // list-group-item-action eklemek istersen, highlight için
                        // div.classList.add('list-group-item-action');
                        
                        div.textContent = item.text;
                        div.dataset.type = item.type;
                        if (item.type === 'question') {
                            div.dataset.id = item.id;
                        } else if (item.type === 'user') {
                            div.dataset.username = item.username;  // data-username özelliğini ekliyoruz
                        }
                        searchResults.appendChild(div);
                    });
                } else {
                    // Sonuç bulunamadı, 'Yeni başlık oluştur' seçeneğini göster
                    var div = document.createElement('div');
                    div.classList.add('list-group-item');
                    div.dataset.type = 'no-results';

                    var span = document.createElement('span');
                    span.textContent = 'Sonuç bulunamadı. ';

                    var a = document.createElement('a');
                    a.href = '#';
                    a.id = 'create-new-question';
                    a.textContent = 'Yeni başlık oluştur';

                    div.appendChild(span);
                    div.appendChild(a);
                    searchResults.appendChild(div);
                }
                searchResults.style.display = 'block';
                currentFocus = -1;  // her yeni sonuç geldiğinde sıfırla
            });
        } else {
            searchResults.style.display = 'none';
        }
    });

    // Fare tıklamasıyla bir öğe seçme
    searchResults.addEventListener('click', function(event) {
        var target = event.target;

        if (target.id === 'create-new-question') {
            event.preventDefault();
            var query = searchInput.value.trim();
            window.location.href = '/add_question_from_search/?q=' + encodeURIComponent(query);
        } else if (target.classList.contains('list-group-item')) {
            var type = target.dataset.type;
            if (type === 'question') {
                var id = target.dataset.id;
                window.location.href = '/question/' + id + '/';
            } else if (type === 'user') {
                var username = target.dataset.username;
                window.location.href = '/profile/' + username + '/';
            }
        }
    });

    // Hide search results when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#search-input') && !event.target.closest('#search-results')) {
            searchResults.style.display = 'none';
        }
    });

    /**
     * ======== OK TUŞLARI VE ENTER DESTEĞİ ========
     */
    searchInput.addEventListener('keydown', function(e) {
        // Mevcut list-group-item'ları al
        var items = searchResults.querySelectorAll('.list-group-item');
        if (!items.length) return;

        if (e.keyCode === 40) {
            // Aşağı ok (arrow down)
            e.preventDefault();
            currentFocus++;
            if (currentFocus >= items.length) currentFocus = 0;
            highlightItem(items);
        }
        else if (e.keyCode === 38) {
            // Yukarı ok (arrow up)
            e.preventDefault();
            currentFocus--;
            if (currentFocus < 0) currentFocus = items.length - 1;
            highlightItem(items);
        }
        else if (e.keyCode === 13) {
            // Enter
            e.preventDefault();
            if (currentFocus > -1) {
                // Seçili item'a tıklamayı simüle et
                items[currentFocus].click();
            } else {
                // Hiçbir item seçili değilse 
                // (isterseniz normal tam arama sayfasına gidebilirsiniz):
                /*
                var q = this.value.trim();
                if (q) {
                  window.location.href = '/search/?q=' + encodeURIComponent(q);
                }
                */
            }
        }
    });

    // "highlightItem" fonksiyonu => tüm item'lardan .active kaldırır, seçiliye ekler
    function highlightItem(items) {
        // Hepsinden "active"i kaldır
        for (var i = 0; i < items.length; i++) {
            items[i].classList.remove('active');
        }
        if (currentFocus >= 0 && currentFocus < items.length) {
            items[currentFocus].classList.add('active');
        }
    }
});
