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
document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var searchResults = document.getElementById('search-results');

    var query = '';

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
            });
        } else {
            searchResults.style.display = 'none';
        }
    });

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
});

