// // search.js
// $(document).ready(function() {
//     var searchInput = $('#search-input');
//     var resultsContainer = $('#search-results');
//     var currentFocus = -1;  // "highlight" için aktif index

//     // Arama kutusuna yazılınca suggestions isteği
//     searchInput.on('input', function() {
//         var query = $(this).val().trim();
//         if (query.length > 0) {
//             $.ajax({
//                 url: '/search_suggestions/',
//                 data: { 'q': query },
//                 dataType: 'json',
//                 success: function(data) {
//                     console.log(data);
//                     showSuggestions(data.suggestions);
//                 },
//                 error: function(xhr, status, error) {
//                     console.error('Arama isteği başarısız oldu:', error);
//                 }
//             });
//         } else {
//             clearSuggestions();
//         }
//     });

//     // Önerileri gösteren fonksiyon
//     function showSuggestions(results) {
//         clearSuggestions();
//         if (results.length > 0) {
//             var suggestionList = $('<ul id="suggestion-list" class="list-group position-absolute w-100"></ul>');
//             results.forEach(function(item) {
//                 var listItem = $('<li class="list-group-item list-group-item-action"></li>');
//                 // 'text' yerine 'label' veya 'text' gibi bir alan kullandığınızdan emin olun.
//                 // Sizin JSON yapınıza göre item.label / item.text olabilir.
//                 // Kodunuzda data.results.push({ 'type': 'question'...'text': '...' }) diyordunuz.
//                 // Dolayısıyla "listItem.text(item.text)" doğru.
//                 listItem.text(item.label || item.text);  
//                 listItem.attr('data-type', item.type);

//                 if (item.type === 'question') {
//                     listItem.attr('data-id', item.id);
//                     listItem.attr('data-url', '/question/' + item.id + '/');
//                 } else if (item.type === 'user') {
//                     listItem.attr('data-username', item.username);
//                     listItem.attr('data-url', '/profile/' + item.username + '/');
//                 } else {
//                     // Diğer tipler için de benzer mantık
//                 }

//                 suggestionList.append(listItem);
//             });
//             resultsContainer.append(suggestionList);
//             currentFocus = -1; // Yeni liste gelince highlight sıfırlıyoruz
//         }
//     }

//     // Önerileri temizle
//     function clearSuggestions() {
//         $('#suggestion-list').remove();
//         currentFocus = -1;
//     }

//     // Tıklama ile bir öğeyi seçmek
//     resultsContainer.on('click', 'li', function() {
//         var url = $(this).attr('data-url');
//         console.log('Tıklanan öğenin URL\'si:', url);
//         if (url) {
//             window.location.href = url;
//         }
//     });

//     // Aşağı-yukarı oklar ve Enter tuşunu dinlemek
//     searchInput.on('keydown', function(e) {
//         console.log("Key pressed:", e.key, e.keyCode);
//         var suggestionList = $('#suggestion-list');
//         var items = suggestionList.find('li');
//         // items: jQuery listesi

//         if (e.keyCode === 40) {
//             // Aşağı ok (arrow down)
//             e.preventDefault();  // cursor hareketini engelle
//             currentFocus++;
//             addActive(items);
//         } else if (e.keyCode === 38) {
//             // Yukarı ok (arrow up)
//             e.preventDefault();
//             currentFocus--;
//             addActive(items);
//         } else if (e.keyCode === 13) {
//             // Enter
//             // Eğer bir öğe seçiliyse, ona tıkla
//             e.preventDefault();  // Form submiti engelliyoruz (isterseniz engellemeyin)
//             if (currentFocus > -1) {
//                 // highlightlı bir öğe varsa
//                 $(items[currentFocus]).trigger('click');
//             } else {
//                 // highlight yoksa?
//                 // isterseniz ilk item'e gidebilir,
//                 // ya da normal bir arama sayfasına yönlendirebilirsiniz.
//                 // Örn: normal arama sayfası /search/?q=<query> yapmak isterseniz:
//                 var query = $(this).val().trim();
//                 if (query.length > 0) {
//                     window.location.href = '/search/?q=' + encodeURIComponent(query);
//                 }
//             }
//         }
//     });

//     // Bir öğeye "active" class ekleyen fonksiyon
//     function addActive(items) {
//         if (!items || !items.length) return;
//         removeActive(items);

//         // Listeyi taşma durumuna göre düzeltelim
//         if (currentFocus >= items.length) currentFocus = 0;
//         if (currentFocus < 0) currentFocus = items.length - 1;

//         // Seçili li'ye "active" verelim
//         $(items[currentFocus]).addClass('active');
//         console.log("Aktif item:", currentFocus, items[currentFocus]);
//     }

//     function removeActive(items) {
//         items.removeClass('active');
//     }

//     // Arama kutusu veya sonuçlar dışında bir yere tıklanırsa önerileri gizle
//     $(document).on('click', function(event) {
//         if (!$(event.target).closest('#search-form').length) {
//             clearSuggestions();
//         }
//     });
// });
