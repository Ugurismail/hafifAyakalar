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

// 1) Tanım butonuna tıklayınca modal aç
document.addEventListener('DOMContentLoaded', function() {
  
    // ----------------------------------------------------------------
    // 1) Genel Değişkenler ve Yardımcı Fonksiyon
    // ----------------------------------------------------------------
    // Modal referansı
    var defModal = new bootstrap.Modal(document.getElementById('definitionModal'));
    
    // Django'da CSRF token'ı cookie'den almak için fonksiyon
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Cookie bu isimle başlıyor mu?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
    
    // ----------------------------------------------------------------
    // 2) "Tanım" Modalını Göster Butonu
    // ----------------------------------------------------------------
    document.getElementById('showDefinitionModalBtn').addEventListener('click', function(e) {
      e.preventDefault();
      defModal.show();
    });
  
    // ----------------------------------------------------------------
    // 3) "Tanım Yap" Sekmesi => Form Submit => createDefinition endpoint'ine POST
    // ----------------------------------------------------------------
    var createDefinitionForm = document.getElementById('createDefinitionForm');
    createDefinitionForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      // Tanım metnini al
      var definitionText = document.getElementById('definitionText').value;
      // Hangi soru altına tanım yapıldığını question_id hidden input’tan al
      var questionId = document.getElementById('answer_form_question_id').value; 
  
      fetch(`/create-definition/${questionId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ definition_text: definitionText })
      })
      .then(res => res.json())
      .then(data => {
         if(data.status === 'success') {
           alert("Tanım kaydedildi!");
           // Modalı kapat
           let modalInstance = bootstrap.Modal.getInstance(defModal._element);
           if (modalInstance) {
             modalInstance.hide();
           }
           // Sayfayı yenile (yeni tanım eklensin, answer kısmında da görebilirsin)
           location.reload();
           // Formu sıfırla
           document.getElementById('definitionText').value = "";
         } else {
           alert("Hata oluştu");
         }
      })
      .catch((err) => {
        console.error(err);
        alert("Sunucu hatası veya ağ hatası oluştu.");
      });
    });
  
    // ----------------------------------------------------------------
    // 4) "Tanım Bul" Sekmesine Geçince => Kullanıcının Tanımlarını GET ile çek
    // ----------------------------------------------------------------
    document.getElementById('tanim-bul-tab').addEventListener('show.bs.tab', function(e) {
      fetch('/get-user-definitions/', {
        method: 'GET'
      })
      .then(res => res.json())
      .then(data => {
        var selectEl = document.getElementById('definitionSelect');
        // Eski seçenekleri temizle
        selectEl.innerHTML = '<option value="">Bir tanım seçiniz...</option>';
  
        // Dönen tanımları <option> şeklinde ekle
        // data.definitions => [{id, question_id, question_text, definition_text}, ...]
        data.definitions.forEach(function(item) {
           // Örnek: "Özgürlük" veya "Özgürlük - (çok iyidir)" diye göstermek istersen
           // opt.textContent = item.question_text + " - " + item.definition_text.substring(0, 30);
           // Ama sadece question_text göstermek istersen:
           var displayLabel = item.question_text;
  
           var opt = document.createElement('option');
           // JS objesini JSON string’e çevirip 'value'ya koyuyoruz.
           // Sonra seçildiğinde "JSON.parse(...)" ile geri alacağız
           opt.value = JSON.stringify(item);
           opt.textContent = displayLabel;
           selectEl.appendChild(opt);
        });
      })
      .catch((err) => {
        console.error(err);
        alert("Tanımlar alınırken hata oluştu.");
      });
    });
  
    // ----------------------------------------------------------------
    // 5) "Tamam" Butonuna Basınca => Seçili Tanımı Alıp Yanıt Textarea'sına (tanim:...) Ekle
    // ----------------------------------------------------------------
    document.getElementById('insertDefinitionBtn').addEventListener('click', function(e) {
      var selectEl = document.getElementById('definitionSelect');
      if(!selectEl.value) return;
  
      // Seçili option’ın value’su JSON string => parse ediyoruz
      var item = JSON.parse(selectEl.value);
      // item => {id, question_id, question_text, definition_text, ...}
      var questionWord = item.question_text;  // "Özgürlük" vb.
      var definitionId = item.id;            // 42 vb.
  
      // Metin içine (tanim:Özgürlük:42) ekleyeceğiz
      var insertStr = `(tanim:${questionWord}:${definitionId})`;
  
      // Ana cevabın yazıldığı textarea (örnek: name="answer_text")
      var answerTextarea = document.querySelector('textarea[name="answer_text"]');
      if(!answerTextarea) {
        alert("Yanıt textarea bulunamadı!");
        return;
      }
  
      // Sonuna ekleyelim
      answerTextarea.value += " " + insertStr; 
  
      // Sonra modalı kapat
      defModal.hide();
    });
  
  }); // DOMContentLoaded sonu
  
  
