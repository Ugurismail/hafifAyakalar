/* base.js */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
}

/**
 * Arama sonuçlarını global bir değişkende tutacağız,
 * böylece Enter'a basıldığında bakabiliriz.
 */
let lastSearchResults = [];

document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var searchResults = document.getElementById('search-results');

    var query = '';
    var currentFocus = -1;  // Ok tuşlarıyla hangi item seçili

    searchInput.addEventListener('input', function() {
        query = this.value.trim();
        if (query.length > 0) {
            fetch('/search/?q=' + encodeURIComponent(query), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                lastSearchResults = data.results;  // Global olarak sakla

                // Önceki sonuçları temizle
                searchResults.innerHTML = '';

                if (data.results.length > 0) {
                    // Gelen tüm sonuçlar için <div> ekle
                    data.results.forEach(function(item) {
                        var div = document.createElement('div');
                        div.classList.add('list-group-item');
                        
                        div.textContent = item.text;
                        div.dataset.type = item.type;
                        if (item.type === 'question') {
                            div.dataset.id = item.id;
                        } else if (item.type === 'user') {
                            div.dataset.username = item.username;
                        }
                        searchResults.appendChild(div);
                    });
                } else {
                    // Sonuç bulunamadı => "Yeni başlık oluştur" seçeneği
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
                currentFocus = -1;
            });
        } else {
            searchResults.style.display = 'none';
            lastSearchResults = [];
        }
    });

    // Fare tıklamasıyla seçim
    searchResults.addEventListener('click', function(event) {
        var target = event.target;
        if (target.id === 'create-new-question') {
            event.preventDefault();
            var q = searchInput.value.trim();
            window.location.href = '/add_question_from_search/?q=' + encodeURIComponent(q);
        } 
        else if (target.classList.contains('list-group-item')) {
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

    // Sayfanın başka yerine tıklayınca listeyi gizle
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#search-input') && !event.target.closest('#search-results')) {
            searchResults.style.display = 'none';
        }
    });

    /**
     * ========== Ok Tuşları ve Enter Desteği ==========
     */
    searchInput.addEventListener('keydown', function(e) {
        // Mevcut list-group-item'lar
        var items = searchResults.querySelectorAll('.list-group-item');

        if (e.keyCode === 40) {
            // Arrow Down
            e.preventDefault();
            currentFocus++;
            if (currentFocus >= items.length) currentFocus = 0;
            highlightItem(items);
        }
        else if (e.keyCode === 38) {
            // Arrow Up
            e.preventDefault();
            currentFocus--;
            if (currentFocus < 0) currentFocus = items.length - 1;
            highlightItem(items);
        }
        else if (e.keyCode === 13) {
            // ====== ENTER'a basıldı ======
            e.preventDefault();

            // 1) Ok tuşlarıyla bir sonuç seçiliyse => tıkla
            if (currentFocus > -1) {
                items[currentFocus].click();
                return;
            }

            // 2) Hiçbir sonuç "aktif" değil => 
            //    Kullanıcının girdiği metinle tam eşleşen bir "question" var mı diye bakalım.
            const typed = searchInput.value.trim().toLowerCase();

            // lastSearchResults içinde "text.toLowerCase() === typed" olan question var mı?
            let exactQuestion = lastSearchResults.find(res => {
                if (res.type === 'question') {
                    return res.text.toLowerCase() === typed;
                }
                return false;
            });

            if (exactQuestion) {
                // Tam eşleşme bulduk => o başlığa git
                window.location.href = '/question/' + exactQuestion.id + '/';
            } else {
                // Tam eşleşme yok => yeni başlık
                // (Arama sonuçlarında başka partial match'ler olabilir ama user Enter basınca 
                //  "ben bu kelimeyle yeni başlık açmak istiyorum" demek.)
                if (typed) {
                    window.location.href = '/add_question_from_search/?q=' + encodeURIComponent(typed);
                }
            }
        }
    });

    function highlightItem(items) {
        // Tümünde 'active'ı temizle
        for (var i = 0; i < items.length; i++) {
            items[i].classList.remove('active');
        }
        if (currentFocus >= 0 && currentFocus < items.length) {
            items[currentFocus].classList.add('active');
        }
    }
});
