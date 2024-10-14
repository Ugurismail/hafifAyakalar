document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.getElementById('search-input');
    var searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', function() {
        var query = this.value;
        if (query.length > 0) {
            fetch('/search/?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    // Arama sonuçlarını doldurun
                    searchResults.innerHTML = '';
                    data.results.forEach(function(item) {
                        var div = document.createElement('div');
                        div.classList.add('list-group-item');
                        div.textContent = item.text;
                        div.dataset.type = item.type;
                        div.dataset.id = item.id;
                        searchResults.appendChild(div);
                    });
                    searchResults.style.display = 'block';
                });
        } else {
            searchResults.style.display = 'none';
        }
    });

    // Arama sonucu tıklandığında
    searchResults.addEventListener('click', function(event) {
        var target = event.target;
        if (target && target.matches('.list-group-item')) {
            var type = target.dataset.type;
            var id = target.dataset.id;
            if (type === 'question') {
                window.location.href = '/question/' + id + '/';
            } else if (type === 'user') {
                window.location.href = '/profile/' + id + '/';
            }
        }
    });

    // Arama sonuçlarını gizleyin
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#search-input') && !event.target.closest('#search-results')) {
            searchResults.style.display = 'none';
        }
    });
});