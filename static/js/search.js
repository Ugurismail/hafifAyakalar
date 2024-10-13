$(document).ready(function() {
    $('#search-input').keyup(function() {
        var query = $(this).val();
        if (query.length > 1) {
            $.ajax({
                url: '/search_suggestions/',
                data: {
                    'q': query
                },
                success: function(data) {
                    // Önerileri göster
                    showSuggestions(data.suggestions);
                }
            });
        } else {
            // Önerileri temizle
            clearSuggestions();
        }
    });

    function showSuggestions(suggestions) {
        // Önerileri göstermek için bir liste oluşturun veya mevcut bir listeyi güncelleyin
        var suggestionList = $('#suggestion-list');
        if (suggestionList.length === 0) {
            suggestionList = $('<ul id="suggestion-list"></ul>');
            $('#search-form').append(suggestionList);
        }
        suggestionList.empty();
        suggestions.forEach(function(suggestion) {
            var item = $('<li></li>').text(suggestion.label);
            item.click(function() {
                window.location.href = suggestion.url;
            });
            suggestionList.append(item);
        });
    }

    function clearSuggestions() {
        $('#suggestion-list').remove();
    }
});
