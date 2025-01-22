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

document.addEventListener('DOMContentLoaded', function() {
  
    // ----------------------------------------------------------------
    // A) Ortak Elemanlar ve Yardımcı Fonksiyonlar
    // ----------------------------------------------------------------
    var defModal = new bootstrap.Modal(document.getElementById('definitionModal'));
    
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
    
    // ----------------------------------------------------------------
    // B) "Tanım" Modalını Açan Buton
    // ----------------------------------------------------------------
    document.getElementById('showDefinitionModalBtn').addEventListener('click', function(e) {
      e.preventDefault();
      defModal.show();
    });
  
    // ----------------------------------------------------------------
    // C) "Tanım Yap" (1. sekme): Form submit => createDefinition endpoint
    // ----------------------------------------------------------------
    var createDefinitionForm = document.getElementById('createDefinitionForm');
    createDefinitionForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      var definitionText = document.getElementById('definitionText').value;
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
           let modalInstance = bootstrap.Modal.getInstance(defModal._element);
           if (modalInstance) {
             modalInstance.hide();
           }
           location.reload();
           document.getElementById('definitionText').value = "";
         } else {
           alert("Hata oluştu");
         }
      })
      .catch(err => {
        console.error(err);
        alert("Sunucu veya ağ hatası oluştu.");
      });
    });
  
    // ----------------------------------------------------------------
    // D) "Tanımlarım" (2. sekme): show.bs.tab => /get-user-definitions/
    // ----------------------------------------------------------------
    document.getElementById('tanim-bul-tab').addEventListener('show.bs.tab', function(e) {
      fetch('/get-user-definitions/', { method: 'GET' })
        .then(res => res.json())
        .then(data => {
          var selectEl = document.getElementById('definitionSelect');
          selectEl.innerHTML = '<option value="">Bir tanım seçiniz...</option>';
          data.definitions.forEach(function(item) {
             // item => {id, question_id, question_text, definition_text}
             var opt = document.createElement('option');
             opt.value = JSON.stringify(item);
             // İster "Özgürlük (çok iyidir...)" gibi gösterebilirsin
             opt.textContent = item.question_text;
             selectEl.appendChild(opt);
          });
        })
        .catch(err => {
          console.error(err);
          alert("Tanımlar alınırken hata oluştu.");
        });
    });
  
    // (D.1) "Tamam" butonu => Seçili tanımı alıp (tanim:kelime:ID) ekle
    document.getElementById('insertDefinitionBtn').addEventListener('click', function(e) {
      var selectEl = document.getElementById('definitionSelect');
      if(!selectEl.value) return;
      var item = JSON.parse(selectEl.value);
      var questionWord = item.question_text;
      var definitionId = item.id;
  
      var answerTextarea = document.querySelector('textarea[name="answer_text"]');
      if(!answerTextarea) {
        alert("Yanıt textarea bulunamadı!");
        return;
      }
  
      var insertStr = `(tanim:${questionWord}:${definitionId})`;
      answerTextarea.value += " " + insertStr; 
      defModal.hide();
    });
  
    // ----------------------------------------------------------------
    // E) "Genel Tanımlar" (3. sekme): Tüm tanımlar + Arama
    // ----------------------------------------------------------------
  
    // Eleman referansları
    var allDefSearchInput = document.getElementById('allDefSearchInput');
    var allDefinitionsList = document.getElementById('allDefinitionsList');
    var insertGlobalDefinitionBtn = document.getElementById('insertGlobalDefinitionBtn');
  
    // (E.1) 3. sekme açıldığında (show.bs.tab)
    document.getElementById('genel-tanim-tab').addEventListener('show.bs.tab', function(e) {
      // Sekme ilk açıldığında "arama kutusu boş" => tüm tanımları listele
      loadGlobalDefinitions("");
    });
  
    // (E.2) Arama kutusuna yazıldıkça => loadGlobalDefinitions( q )
    allDefSearchInput.addEventListener('keyup', function(e) {
      var query = allDefSearchInput.value.trim();
      loadGlobalDefinitions(query);
    });
  
    // (E.3) Tanımları listeleme fonksiyonu
    function loadGlobalDefinitions(query) {
      // /get-all-definitions/?q=... endpoint'ine GET request
      var url = '/get-all-definitions/';
      if(query) {
        url += '?q=' + encodeURIComponent(query);
      }
  
      fetch(url)
        .then(res => res.json())
        .then(data => {
          // data.definitions => [{id, question_text, definition_text, username}, ...]
          // Listeyi dolduralım
          allDefinitionsList.innerHTML = '';
          if(data.definitions.length === 0) {
            allDefinitionsList.innerHTML = '<li class="list-group-item text-muted">Hiç tanım bulunamadı.</li>';
            return;
          }
  
          data.definitions.forEach(function(d) {
            // Her tanımı <li> içinde radio buton ile gösteriyoruz
            // => <input type="radio" name="globalDef" value='{"id":..., "question_text":"...", ...}' />
            // Sorunun metni + tanımın kısaltılmış versiyonu + kullanıcı adını gösterebilirsin
            var li = document.createElement('li');
            li.classList.add('list-group-item');
  
            // JSON veriyi saklamak için string’e çevir
            let itemJson = JSON.stringify(d);
            let shortDef = d.definition_text;
            if(shortDef.length > 50) {
              shortDef = shortDef.substring(0, 50) + '...';
            }
  
            li.innerHTML = `
              <div class="form-check">
                <input class="form-check-input" type="radio" name="globalDef" value='${itemJson}'>
                <label class="form-check-label">
                  <strong>${d.question_text}</strong> <em>(${shortDef})</em> 
                  <small class="text-muted">- by ${d.username}</small>
                </label>
              </div>
            `;
            allDefinitionsList.appendChild(li);
          });
        })
        .catch(err => {
          console.error(err);
          alert("Genel tanımlar yüklenirken hata oluştu.");
        });
    }
  
    // (E.4) "Seçili Tanımı Ekle" butonuna tıklayınca
    insertGlobalDefinitionBtn.addEventListener('click', function(e) {
      // Seçili radio butonunu bul
      var checkedRadio = document.querySelector('input[name="globalDef"]:checked');
      if(!checkedRadio) {
        alert("Lütfen bir tanım seçin.");
        return;
      }
      var item = JSON.parse(checkedRadio.value);
      // item => { id, question_text, definition_text, username }
  
      var answerTextarea = document.querySelector('textarea[name="answer_text"]');
      if(!answerTextarea) {
        alert("Yanıt textarea bulunamadı!");
        return;
      }
  
      // (tanim:kelime:ID)
      var insertStr = `(tanim:${item.question_text}:${item.id})`;
      answerTextarea.value += " " + insertStr;
  
      defModal.hide();
    });
  
  });
  