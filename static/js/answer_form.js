// answer_form.js

document.addEventListener('DOMContentLoaded', function() {
  //==================================================================
  // A) METİN BİÇİMLENDİRME BUTONLARI (BOLD, ITALIC)
  //==================================================================
  var formatButtons = document.querySelectorAll('.format-btn');
  formatButtons.forEach(function(button) {
      button.addEventListener('click', function() {
          var format = this.getAttribute('data-format');
          var textarea = document.getElementById('id_answer_text');
          applyFormat(textarea, format);
      });
  });

  function applyFormat(textarea, format) {
      if (!textarea) return;
      var start = textarea.selectionStart;
      var end   = textarea.selectionEnd;
      var selectedText = textarea.value.substring(start, end);
      var before = textarea.value.substring(0, start);
      var after  = textarea.value.substring(end);

      var formattedText = selectedText;
      if (format === 'bold') {
          formattedText = '**' + selectedText + '**';
      } else if (format === 'italic') {
          formattedText = '*' + selectedText + '*';
      }

      textarea.value = before + formattedText + after;
      textarea.focus();
      // Seçili alanı yeniden belirle
      textarea.selectionStart = start;
      textarea.selectionEnd   = start + formattedText.length;
  }


  //==================================================================
  // B) HARİCİ LİNK EKLEME (MODAL)
  //==================================================================
  var linkModalElem = document.getElementById('linkModal');
  if (linkModalElem) {
    var linkModal    = new bootstrap.Modal(linkModalElem);
    var insertLinkBtn= document.querySelector('.insert-link-btn');
    var linkForm     = document.getElementById('link-form');

    if (insertLinkBtn && linkForm) {
      insertLinkBtn.addEventListener('click', function() {
        linkModal.show();
        linkForm.reset();
      });

      linkForm.addEventListener('submit', function(event) {
        event.preventDefault();
        var url  = document.getElementById('link-url').value.trim();
        var text = document.getElementById('link-text').value.trim();
        if (url && text) {
            var textarea = document.getElementById('id_answer_text');
            if (!textarea) return;
            var start = textarea.selectionStart;
            var end   = textarea.selectionEnd;
            var before= textarea.value.substring(0, start);
            var after = textarea.value.substring(end);
            var linkMarkdown = '[' + text + '](' + url + ')';
            textarea.value = before + linkMarkdown + after;
            textarea.focus();
            textarea.selectionStart = start;
            textarea.selectionEnd   = start + linkMarkdown.length;
            linkModal.hide();
        }
      });
    }
  }


  //==================================================================
  // C) (bkz:...) REFERANS EKLEME (MODAL)
  //==================================================================
  var referenceModalElem = document.getElementById('referenceModal');
  if (referenceModalElem) {
    var referenceModal       = new bootstrap.Modal(referenceModalElem);
    var insertReferenceBtn   = document.querySelector('.insert-reference-btn');
    var referenceSearchInput = document.getElementById('reference-search-input');
    var referenceSearchResults= document.getElementById('reference-search-results');
    var noResultsDiv         = document.getElementById('no-results');
    var addCurrentQueryBtn   = document.getElementById('add-current-query');

    if (insertReferenceBtn) {
      insertReferenceBtn.addEventListener('click', function() {
          referenceModal.show();
          if (referenceSearchInput) {
            referenceSearchInput.value = '';
          }
          if (referenceSearchResults) {
            referenceSearchResults.innerHTML = '';
          }
          if (noResultsDiv) {
            noResultsDiv.style.display = 'none';
          }
      });
    }

    // Arama
    if (referenceSearchInput && referenceSearchResults && noResultsDiv) {
      referenceSearchInput.addEventListener('input', function() {
        var query = this.value.trim();
        if (query.length > 0) {
          fetch('/reference-search/?q=' + encodeURIComponent(query), {
              headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
          .then(response => response.json())
          .then(data => {
              referenceSearchResults.innerHTML = '';
              if (data.results && data.results.length > 0) {
                  noResultsDiv.style.display = 'none';
                  data.results.forEach(function(item) {
                      var div = document.createElement('div');
                      div.classList.add('list-group-item');
                      div.textContent = item.text;
                      div.dataset.questionId = item.id;
                      referenceSearchResults.appendChild(div);
                  });
              } else {
                  noResultsDiv.style.display = 'block';
                  referenceSearchResults.innerHTML = '';
              }
          });
        } else {
          referenceSearchResults.innerHTML = '';
          noResultsDiv.style.display = 'none';
        }
      });

      // Arama sonuçlarından birine tıklayınca
      referenceSearchResults.addEventListener('click', function(event) {
        var target = event.target;
        if (target && target.matches('.list-group-item')) {
            insertBkzReference(target.textContent);
            referenceModal.hide();
        }
      });

      // Mevcut sorguyu ekle
      if (addCurrentQueryBtn) {
        addCurrentQueryBtn.addEventListener('click', function() {
          var query = referenceSearchInput.value.trim();
          if (query.length > 0) {
            insertBkzReference(query);
            referenceModal.hide();
          }
        });
      }
    }

    function insertBkzReference(text) {
      var textarea = document.getElementById('id_answer_text');
      if (!textarea) return;
      var start = textarea.selectionStart;
      var end   = textarea.selectionEnd;
      var before= textarea.value.substring(0, start);
      var after = textarea.value.substring(end);
      var referenceText = '(bkz: ' + text + ')';
      textarea.value = before + referenceText + after;
      textarea.focus();
      textarea.selectionStart = start;
      textarea.selectionEnd   = start + referenceText.length;
    }
  }


  //==================================================================
  // D) (ref:...) BUTONU
  //==================================================================
  var insertRefLinkBtn = document.querySelector('.insert-ref-link-btn');
  if (insertRefLinkBtn) {
    insertRefLinkBtn.addEventListener('click', function() {
      var textarea = document.getElementById('id_answer_text');
      if (!textarea) return;

      var selectedText = getSelectedText(textarea);
      if (selectedText) {
          var refMarkup = `(ref:${selectedText})`;
          insertTextAtCursor(textarea, refMarkup);
      } else {
          alert('Lütfen renkli bağlantı yapmak istediğiniz metni seçiniz.');
      }
    });
  }

  function getSelectedText(textarea) {
    if (!textarea) return '';
    var start = textarea.selectionStart;
    var end   = textarea.selectionEnd;
    return textarea.value.substring(start, end);
  }

  function insertTextAtCursor(textarea, text) {
    var start = textarea.selectionStart;
    var end   = textarea.selectionEnd;
    var before= textarea.value.substring(0, start);
    var after = textarea.value.substring(end);
    textarea.value = before + text + after;
    textarea.selectionStart = textarea.selectionEnd = start + text.length;
    textarea.focus();
  }


  //==================================================================
  // E) TANIM MODALI (3 SEKME)
  //==================================================================
  var definitionModalElem = document.getElementById('definitionModal');
  if (!definitionModalElem) {
    // "Tanım" modalı yoksa çık
    return;
  }
  var defModal = new bootstrap.Modal(definitionModalElem);

  // Modalı açan buton
  var showDefinitionModalBtn = document.getElementById('showDefinitionModalBtn');
  if (showDefinitionModalBtn) {
    showDefinitionModalBtn.addEventListener('click', function(e) {
      e.preventDefault();
      defModal.show();
    });
  }

  // (E.1) TANIM YAP Sekmesi
  var createDefinitionForm = document.getElementById('createDefinitionForm');
  if (createDefinitionForm) {
    createDefinitionForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var definitionText = document.getElementById('definitionText').value;
      var questionIdElem = document.getElementById('answer_form_question_id');
      if (!questionIdElem) {
        alert("Soru ID bulunamadı (answer_form_question_id).");
        return;
      }
      var questionId = questionIdElem.value;

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
         if (data.status === 'success') {
           alert("Tanım kaydedildi!");
           // Modal’ı kapat
           let modalInstance = bootstrap.Modal.getInstance(definitionModalElem);
           if (modalInstance) {
             modalInstance.hide();
           }
           document.getElementById('definitionText').value = "";
           // Sayfayı yenile
           location.reload();
         } else {
           alert("Hata oluştu: " + JSON.stringify(data.errors || data));
         }
      })
      .catch(err => {
        console.error(err);
        alert("Sunucu veya ağ hatası oluştu.");
      });
    });
  }


  // (E.2) TANIMLARIM Sekmesi (Kullanıcı Tanımları)
  // Arama + liste + radio buton + sayfalama
  var userDefTab           = document.getElementById('tanim-bul-tab');
  var userDefSearchInput   = document.getElementById('userDefSearchInput');
  var userDefinitionsList  = document.getElementById('userDefinitionsList');
  var userDefPagination    = document.getElementById('userDefPagination');
  var insertUserDefinitionBtn = document.getElementById('insertUserDefinitionBtn');

  if (userDefTab) {
    // Sekme açıldığında => 1. sayfa, boş arama
    userDefTab.addEventListener('show.bs.tab', function(e) {
      loadUserDefinitions(1, "");
      if (userDefSearchInput) {
        userDefSearchInput.value = "";
      }
    });
  }

  if (userDefSearchInput) {
    userDefSearchInput.addEventListener('keyup', function() {
      var q = this.value.trim();
      loadUserDefinitions(1, q);
    });
  }

  function loadUserDefinitions(page, q) {
    let url = `/get-user-definitions/?page=${page}`;
    if (q) url += `&q=${encodeURIComponent(q)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        // data: { definitions: [...], current_page, total_pages, ... }
        if (userDefinitionsList) {
          userDefinitionsList.innerHTML = '';
          if (!data.definitions || data.definitions.length === 0) {
            userDefinitionsList.innerHTML = `<li class="list-group-item text-muted">Hiç tanım bulunamadı.</li>`;
          } else {
            data.definitions.forEach(function(d) {
              let shortDef = d.definition_text;
              if (shortDef.length > 50) {
                shortDef = shortDef.substring(0,50) + '...';
              }
              let itemJson = JSON.stringify(d);
              let li = document.createElement('li');
              li.classList.add('list-group-item');
              li.innerHTML = `
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="userDef" value='${itemJson}'>
                  <label class="form-check-label">
                    <strong>${d.question_text}</strong>
                    <em>(${shortDef})</em>
                    <small class="text-muted">[Ben:${d.usage_count_self}, Tüm:${d.usage_count_all}]</small>
                  </label>
                </div>
              `;
              userDefinitionsList.appendChild(li);
            });
          }
        }

        // Sayfalama
        if (userDefPagination) {
          userDefPagination.innerHTML = '';
          if (data.total_pages > 1) {
            // Prev
            if (data.current_page > 1) {
              let prevBtn = document.createElement('button');
              prevBtn.classList.add('btn','btn-sm','btn-outline-secondary','me-2');
              prevBtn.textContent = 'Önceki';
              prevBtn.addEventListener('click', function() {
                loadUserDefinitions(data.current_page - 1, userDefSearchInput.value.trim());
              });
              userDefPagination.appendChild(prevBtn);
            }
            // sayfa info
            let pageInfo = document.createElement('span');
            pageInfo.textContent = `Sayfa ${data.current_page} / ${data.total_pages}`;
            pageInfo.classList.add('me-2');
            userDefPagination.appendChild(pageInfo);

            // Next
            if (data.current_page < data.total_pages) {
              let nextBtn = document.createElement('button');
              nextBtn.classList.add('btn','btn-sm','btn-outline-secondary');
              nextBtn.textContent = 'Sonraki';
              nextBtn.addEventListener('click', function() {
                loadUserDefinitions(data.current_page + 1, userDefSearchInput.value.trim());
              });
              userDefPagination.appendChild(nextBtn);
            }
          }
        }
      })
      .catch(err => {
        console.error(err);
        alert("Tanımlar (kullanıcı) yüklenirken hata oluştu.");
      });
  }

  if (insertUserDefinitionBtn) {
    insertUserDefinitionBtn.addEventListener('click', function() {
      let checked = document.querySelector('input[name="userDef"]:checked');
      if (!checked) {
        alert("Lütfen bir tanım seçiniz.");
        return;
      }
      let item = JSON.parse(checked.value);
      let questionWord = item.question_text;
      let definitionId = item.id;

      let answerTextarea = document.querySelector('textarea[name="answer_text"]');
      if (!answerTextarea) {
        alert("Yanıt textarea bulunamadı!");
        return;
      }

      let insertStr = `(tanim:${questionWord}:${definitionId})`;
      answerTextarea.value += ` ${insertStr}`;

      // Modal kapat
      let defModalInstance = bootstrap.Modal.getInstance(definitionModalElem);
      if (defModalInstance) {
        defModalInstance.hide();
      }
    });
  }


  // (E.3) GENEL TANIMLAR Sekmesi
  var allDefTab               = document.getElementById('genel-tanim-tab');
  var allDefSearchInput       = document.getElementById('allDefSearchInput');
  var allDefinitionsList      = document.getElementById('allDefinitionsList');
  var allDefPagination        = document.getElementById('allDefPagination');
  var insertGlobalDefinitionBtn = document.getElementById('insertGlobalDefinitionBtn');

  if (allDefTab) {
    allDefTab.addEventListener('show.bs.tab', function(e) {
      loadGlobalDefinitions(1, "");
      if(allDefSearchInput) {
        allDefSearchInput.value = "";
      }
    });
  }

  if (allDefSearchInput) {
    allDefSearchInput.addEventListener('keyup', function() {
      var query = this.value.trim();
      loadGlobalDefinitions(1, query);
    });
  }

  function loadGlobalDefinitions(page, query) {
    let url = '/get-all-definitions/?page=' + page;
    if (query) {
      url += '&q=' + encodeURIComponent(query);
    }

    fetch(url)
      .then(res => res.json())
      .then(data => {
        // data.definitions => [ {id, question_text, definition_text, username, usage_count_all}, ... ]
        if (allDefinitionsList) {
          allDefinitionsList.innerHTML = '';
          if (!data.definitions || data.definitions.length === 0) {
            allDefinitionsList.innerHTML = '<li class="list-group-item text-muted">Hiç tanım bulunamadı.</li>';
          } else {
            data.definitions.forEach(function(d) {
              let shortDef = d.definition_text;
              if (shortDef.length > 50) {
                shortDef = shortDef.substring(0,50) + '...';
              }
              let itemJson = JSON.stringify(d);
              let li = document.createElement('li');
              li.classList.add('list-group-item');
              li.innerHTML = `
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="globalDef" value='${itemJson}'>
                  <label class="form-check-label">
                    <strong>${d.question_text}</strong>
                    <em>(${shortDef})</em>
                    <small class="text-muted">by ${d.username}</small>
                    <small class="ms-2">[${d.usage_count_all} kez kullanılmış]</small>
                  </label>
                </div>
              `;
              allDefinitionsList.appendChild(li);
            });
          }
        }

        // Sayfalama
        if (allDefPagination) {
          allDefPagination.innerHTML = '';
          if (data.total_pages > 1) {
            // Prev
            if (data.current_page > 1) {
              let prevBtn = document.createElement('button');
              prevBtn.textContent = 'Önceki';
              prevBtn.classList.add('btn','btn-sm','btn-outline-secondary','me-2');
              prevBtn.addEventListener('click', function(){
                loadGlobalDefinitions(data.current_page - 1, allDefSearchInput.value.trim());
              });
              allDefPagination.appendChild(prevBtn);
            }
            // Page Info
            let pageInfo = document.createElement('span');
            pageInfo.textContent = `Sayfa ${data.current_page} / ${data.total_pages}`;
            pageInfo.classList.add('me-2');
            allDefPagination.appendChild(pageInfo);

            // Next
            if (data.current_page < data.total_pages) {
              let nextBtn = document.createElement('button');
              nextBtn.textContent = 'Sonraki';
              nextBtn.classList.add('btn','btn-sm','btn-outline-secondary');
              nextBtn.addEventListener('click', function(){
                loadGlobalDefinitions(data.current_page + 1, allDefSearchInput.value.trim());
              });
              allDefPagination.appendChild(nextBtn);
            }
          }
        }
      })
      .catch(err => {
        console.error(err);
        alert("Genel tanımlar alınırken hata oluştu.");
      });
  }

  if (insertGlobalDefinitionBtn) {
    insertGlobalDefinitionBtn.addEventListener('click', function(e) {
      var checkedRadio = document.querySelector('input[name="globalDef"]:checked');
      if(!checkedRadio) {
        alert("Lütfen bir tanım seçin.");
        return;
      }
      var item = JSON.parse(checkedRadio.value);
      // item => {id, question_text, definition_text, usage_count_all, username...}
      var answerTextarea = document.querySelector('textarea[name="answer_text"]');
      if(!answerTextarea) {
        alert("Yanıt textarea bulunamadı!");
        return;
      }
      var insertStr = `(tanim:${item.question_text}:${item.id})`;
      answerTextarea.value += " " + insertStr;

      let defModalInstance = bootstrap.Modal.getInstance(definitionModalElem);
      if (defModalInstance) {
        defModalInstance.hide();
      }
    });
  }

});
