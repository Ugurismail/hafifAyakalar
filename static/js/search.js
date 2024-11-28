$(document).ready(function() {
    var searchInput = $('#search-input');
    var resultsContainer = $('#search-results');

    searchInput.on('input', function() {
        var query = $(this).val().trim();
        if (query.length > 0) {
            $.ajax({
                url: '/search_suggestions/',  // Burada '/search_suggestions/' kullanıyoruz
                data: {
                    'q': query
                },
                dataType: 'json',
                success: function(data) {
                    console.log(data);  // Gelen veriyi konsola yazdırıyoruz
                    showSuggestions(data.suggestions);
                },
                error: function(xhr, status, error) {
                    console.error('Arama isteği başarısız oldu:', error);
                }
            });
        } else {
            clearSuggestions();
        }
    });

// search.js

function showSuggestions(results) {
    clearSuggestions();
    if (results.length > 0) {
        var suggestionList = $('<ul id="suggestion-list" class="list-group position-absolute w-100"></ul>');
        results.forEach(function(item) {
            var listItem = $('<li class="list-group-item list-group-item-action"></li>');
            listItem.text(item.text);
            listItem.attr('data-type', item.type);
            if (item.type === 'question') {
                listItem.attr('data-id', item.id);
                listItem.attr('data-url', '/question/' + item.id + '/');
            } else if (item.type === 'user') {
                listItem.attr('data-username', item.username);
                listItem.attr('data-url', '/profile/' + item.username + '/');
            }
            suggestionList.append(listItem);
        });
        resultsContainer.append(suggestionList);
    }
}


    function clearSuggestions() {
        $('#suggestion-list').remove();
    }

    // Sonuçlara tıklama işlemi
    resultsContainer.on('click', 'li', function() {
        var url = $(this).attr('data-url');
        console.log('Tıklanan öğenin URL\'si:', url);  // URL'yi konsola yazdırıyoruz
        if (url) {
            window.location.href = url;
        }
    });

    // Arama kutusu veya sonuçlar dışında bir yere tıklandığında önerileri gizle
    $(document).on('click', function(event) {
        if (!$(event.target).closest('#search-form').length) {
            clearSuggestions();
        }
    });
});
