document.addEventListener('DOMContentLoaded', function() {
    // Mevcut metin alanını takip etmek için değişken
    let currentTextarea = null;

    // Link ve Referans Modallarını tanımlayın
    const linkModalElement = document.getElementById('linkModal');
    const referenceModalElement = document.getElementById('referenceModal');
    let linkModal = null;
    let referenceModal = null;

    // Bootstrap modallarını başlatın (eğer varsa)
    if (linkModalElement) {
        linkModal = new bootstrap.Modal(linkModalElement);
    }
    if (referenceModalElement) {
        referenceModal = new bootstrap.Modal(referenceModalElement);
    }

    // Formatlama Butonları (Kalın, İtalik)
    const formatBtns = document.querySelectorAll('.format-btn');
    formatBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentTextarea = this.closest('form').querySelector('textarea');
            const format = this.getAttribute('data-format');
            let tag = '';
            if (format === 'bold') {
                tag = 'strong';
            } else if (format === 'italic') {
                tag = 'em';
            }
            if (tag && currentTextarea) {
                wrapSelectionWithTag(currentTextarea, tag);
                currentTextarea.focus();
            }
        });
    });

    // Link Ekleme Butonu
    const insertLinkBtns = document.querySelectorAll('.insert-link-btn');
    insertLinkBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentTextarea = this.closest('form').querySelector('textarea');
            if (linkModal) {
                linkModal.show();
            }
        });
    });

    // Link Ekleme Formu
    const linkForm = document.getElementById('link-form');
    if (linkForm) {
        linkForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const url = document.getElementById('link-url').value.trim();
            const text = document.getElementById('link-text').value.trim();
            if (url && text && currentTextarea) {
                const linkMarkup = <a href="${url}">${text}</a>;
                insertAtCursor(currentTextarea, linkMarkup);
                linkModal.hide();
                linkForm.reset();
            }
        });
    }

    // "(bkz:soru)" Butonu
    const insertReferenceBtns = document.querySelectorAll('.insert-reference-btn');
    insertReferenceBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentTextarea = this.closest('form').querySelector('textarea');
            if (referenceModal) {
                referenceModal.show();
            }
        });
    });

    // Referans Arama İşlevi
    const referenceSearchInput = document.getElementById('reference-search-input');
    const referenceSearchResults = document.getElementById('reference-search-results');

    if (referenceSearchInput && referenceSearchResults) {
        referenceSearchInput.addEventListener('input', function() {
            const query = referenceSearchInput.value.trim();
            if (query.length > 1) {
                fetch(/search/?q=${encodeURIComponent(query)}&ajax=1)
                    .then(response => response.json())
                    .then(data => {
                        referenceSearchResults.innerHTML = '';
                        if (data.results && data.results.length > 0) {
                            const ul = document.createElement('ul');
                            ul.classList.add('list-group');
                            data.results.forEach(question => {
                                const li = document.createElement('li');
                                li.classList.add('list-group-item');
                                li.textContent = question.question_text;
                                li.addEventListener('click', function() {
                                    const referenceMarkup = (bkz: <a href="/question/${question.id}/">${question.question_text}</a>);
                                    insertAtCursor(currentTextarea, referenceMarkup);
                                    referenceModal.hide();
                                    referenceSearchInput.value = '';
                                    referenceSearchResults.innerHTML = '';
                                });
                                ul.appendChild(li);
                            });
                            referenceSearchResults.appendChild(ul);
                        } else {
                            referenceSearchResults.innerHTML = '<p>Sonuç bulunamadı.</p>';
                        }
                    })
                    .catch(error => {
                        console.error('Referans arama sırasında hata oluştu:', error);
                    });
            } else {
                referenceSearchResults.innerHTML = '';
            }
        });
    }

    // Seçili metni etiketle sarmalama fonksiyonu
    function wrapSelectionWithTag(textarea, tag) {
        const startPos = textarea.selectionStart || 0;
        const endPos = textarea.selectionEnd || 0;
        const selectedText = textarea.value.substring(startPos, endPos);
        const beforeValue = textarea.value.substring(0, startPos);
        const afterValue = textarea.value.substring(endPos);
        const newText = <${tag}>${selectedText}</${tag}>;
        textarea.value = beforeValue + newText + afterValue;
        textarea.selectionStart = startPos;
        textarea.selectionEnd = startPos + newText.length;
    }

    // İmleç konumuna metin ekleme fonksiyonu
    function insertAtCursor(textarea, text) {
        const startPos = textarea.selectionStart || 0;
        const endPos = textarea.selectionEnd || 0;
        const beforeValue = textarea.value.substring(0, startPos);
        const afterValue = textarea.value.substring(endPos);
        textarea.value = beforeValue + text + afterValue;
        textarea.selectionStart = textarea.selectionEnd = startPos + text.length;
    }
});