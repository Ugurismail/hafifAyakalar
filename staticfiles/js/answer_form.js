// answer_form.js

document.addEventListener('DOMContentLoaded', function() {
    // Metin Biçimlendirme Butonları
    var formatButtons = document.querySelectorAll('.format-btn');
    formatButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var format = this.getAttribute('data-format');
            var textarea = document.getElementById('id_answer_text');
            applyFormat(textarea, format);
        });
    });

    function applyFormat(textarea, format) {
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var selectedText = textarea.value.substring(start, end);
        var before = textarea.value.substring(0, start);
        var after = textarea.value.substring(end);
        var formattedText;

        if (format === 'bold') {
            formattedText = '**' + selectedText + '**';
        } else if (format === 'italic') {
            formattedText = '*' + selectedText + '*';
        }

        textarea.value = before + formattedText + after;
        textarea.focus();
        textarea.selectionStart = start;
        textarea.selectionEnd = start + formattedText.length;
    }

    // Link Ekleme Modali
    var linkModal = new bootstrap.Modal(document.getElementById('linkModal'));
    var insertLinkBtn = document.querySelector('.insert-link-btn');
    var linkForm = document.getElementById('link-form');

    insertLinkBtn.addEventListener('click', function() {
        linkModal.show();
        // Formu sıfırla
        linkForm.reset();
    });

    linkForm.addEventListener('submit', function(event) {
        event.preventDefault();
        var url = document.getElementById('link-url').value.trim();
        var text = document.getElementById('link-text').value.trim();
        if (url && text) {
            var textarea = document.getElementById('id_answer_text');
            var start = textarea.selectionStart;
            var end = textarea.selectionEnd;
            var before = textarea.value.substring(0, start);
            var after = textarea.value.substring(end);
            var linkMarkdown = '[' + text + '](' + url + ')';
            textarea.value = before + linkMarkdown + after;
            textarea.focus();
            textarea.selectionStart = start;
            textarea.selectionEnd = start + linkMarkdown.length;
            linkModal.hide();
        }
    });

    // Referans Ekleme Modali
    var referenceModal = new bootstrap.Modal(document.getElementById('referenceModal'));
    var insertReferenceBtn = document.querySelector('.insert-reference-btn');
    var referenceSearchInput = document.getElementById('reference-search-input');
    var referenceSearchResults = document.getElementById('reference-search-results');
    var noResultsDiv = document.getElementById('no-results');
    var addCurrentQueryBtn = document.getElementById('add-current-query');

    insertReferenceBtn.addEventListener('click', function() {
        referenceModal.show();
        referenceSearchInput.value = '';
        referenceSearchResults.innerHTML = '';
        noResultsDiv.style.display = 'none';
    });

    referenceSearchInput.addEventListener('input', function() {
        var query = this.value.trim();
        if (query.length > 0) {
            fetch('/reference-search/?q=' + encodeURIComponent(query), {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                referenceSearchResults.innerHTML = '';
                if (data.results.length > 0) {
                    noResultsDiv.style.display = 'none';
                    data.results.forEach(function(item) {
                        var div = document.createElement('div');
                        div.classList.add('list-group-item');
                        div.textContent = item.text;
                        div.dataset.questionId = item.id;
                        referenceSearchResults.appendChild(div);
                    });
                } else {
                    // Sonuç bulunamadığında
                    noResultsDiv.style.display = 'block';
                    referenceSearchResults.innerHTML = '';
                }
            });
        } else {
            referenceSearchResults.innerHTML = '';
            noResultsDiv.style.display = 'none';
        }
    });

    // Arama Sonuçlarına Tıklama İşlemi
    referenceSearchResults.addEventListener('click', function(event) {
        var target = event.target;
        if (target && target.matches('.list-group-item')) {
            var questionText = target.textContent;
            insertReference(questionText);
            referenceModal.hide();
        }
    });

    // Mevcut Sorguyu Referans Olarak Ekleme
    addCurrentQueryBtn.addEventListener('click', function() {
        var query = referenceSearchInput.value.trim();
        if (query.length > 0) {
            insertReference(query);
            referenceModal.hide();
        }
    });

    function insertReference(text) {
        var textarea = document.getElementById('id_answer_text');
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var before = textarea.value.substring(0, start);
        var after = textarea.value.substring(end);
        var referenceText = '(bkz: ' + text + ')';
        textarea.value = before + referenceText + after;
        textarea.focus();
        textarea.selectionStart = start;
        textarea.selectionEnd = start + referenceText.length;
    }
});

document.addEventListener('DOMContentLoaded', function(){
    const insertRefLinkBtn = document.querySelector('.insert-ref-link-btn');
    const answerTextArea = document.querySelector('#id_answer_text'); // Formdaki textarea'nın id'si

    if (insertRefLinkBtn && answerTextArea) {
        insertRefLinkBtn.addEventListener('click', function() {
            const selectedText = getSelectedText(answerTextArea);
            if (selectedText) {
                const refMarkup = `(ref:${selectedText})`;
                insertTextAtCursor(answerTextArea, refMarkup);
            } else {
                alert('Lütfen renkli bağlantı yapmak istediğiniz metni seçiniz.');
            }
        });
    }

    function getSelectedText(textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        return textarea.value.substring(start, end);
    }

    function insertTextAtCursor(textarea, text) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const before = textarea.value.substring(0, start);
        const after = textarea.value.substring(end);
        textarea.value = before + text + after;
        textarea.selectionStart = textarea.selectionEnd = start + text.length;
        textarea.focus();
    }
});
