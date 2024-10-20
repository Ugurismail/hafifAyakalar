// static/js/base.js
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
                // Clear previous results
                searchResults.innerHTML = '';
                if (data.results.length > 0) {
                    data.results.forEach(function(item) {
                        var div = document.createElement('div');
                        div.classList.add('list-group-item');
                        div.textContent = item.text;
                        div.dataset.type = item.type;
                        div.dataset.id = item.id;
                        searchResults.appendChild(div);
                    });
                } else {
                    // No results found, show 'Create new topic' option
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

    // Handle Enter key
    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            var firstResult = searchResults.querySelector('.list-group-item');
            if (firstResult) {
                var type = firstResult.dataset.type;
                var id = firstResult.dataset.id;
                if (type === 'question') {
                    window.location.href = '/question/' + id + '/';
                } else if (type === 'user') {
                    window.location.href = '/profile/' + id + '/';
                } else if (type === 'no-results') {
                    // Redirect to 'add_question_from_search'
                    window.location.href = '/add_question_from_search/?q=' + encodeURIComponent(query);
                }
            } else {
                // No results at all, redirect to 'add_question_from_search'
                window.location.href = '/add_question_from_search/?q=' + encodeURIComponent(query);
            }
        }
    });

    // Handle clicks on search results
    searchResults.addEventListener('click', function(event) {
        var target = event.target;
        if (target && target.id === 'create-new-question') {
            event.preventDefault();
            // Redirect to 'add_question_from_search'
            window.location.href = '/add_question_from_search/?q=' + encodeURIComponent(query);
        } else if (target && target.matches('.list-group-item')) {
            var type = target.dataset.type;
            var id = target.dataset.id;
            if (type === 'question') {
                window.location.href = '/question/' + id + '/';
            } else if (type === 'user') {
                window.location.href = '/profile/' + id + '/';
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
