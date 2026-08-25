(function(){
  "use strict";

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- dropzone ---------------- */
  var dropzone = document.getElementById('dropzone');
  var fileInput = document.getElementById('file-input');
  var dzIcon = document.getElementById('dz-icon');
  var dzPrimary = document.getElementById('dz-primary');
  var dzSecondary = document.getElementById('dz-secondary');
  var dzBrowse = document.getElementById('dz-browse');
  var formStatus = document.getElementById('form-status');
  var generateBtn = document.getElementById('generate-btn');
  var MAX_BYTES = 10 * 1024 * 1024;

  function resetDropzoneVisual(){
    dropzone.classList.remove('dragover','has-file','error','dz-uploading');
  }

  function showIdle(){
    resetDropzoneVisual();
    dzIcon.textContent = '↓';
    dzPrimary.textContent = 'Drop résumé here';
    dzSecondary.innerHTML = 'or <span class="dz-browse" id="dz-browse-2">browse files</span>';
    formStatus.textContent = 'no file selected';
    formStatus.classList.remove('error');
    generateBtn.disabled = true;
    var b = document.getElementById('dz-browse-2');
    if(b) b.addEventListener('click', function(e){ e.stopPropagation(); fileInput.click(); });
  }

  function showFile(file){
    resetDropzoneVisual();
    dropzone.classList.add('has-file');
    dzIcon.textContent = '✓';
    dzPrimary.textContent = 'File ready';
    var kb = (file.size/1024).toFixed(0);
    dzSecondary.innerHTML = '<span class="dz-secondary filename">' + escapeHtml(file.name) + ' — ' + kb + ' kb</span>';
    formStatus.innerHTML = '<span class="ok">✓ ready to generate</span>';
    formStatus.classList.remove('error');
    generateBtn.disabled = false;
  }

  function showError(msg){
    resetDropzoneVisual();
    dropzone.classList.add('error');
    dzIcon.textContent = '!';
    dzPrimary.textContent = msg;
    dzSecondary.innerHTML = 'try again — or <span class="dz-browse" id="dz-browse-3">browse files</span>';
    formStatus.textContent = msg;
    formStatus.classList.add('error');
    generateBtn.disabled = true;
    var b = document.getElementById('dz-browse-3');
    if(b) b.addEventListener('click', function(e){ e.stopPropagation(); fileInput.click(); });
    setTimeout(function(){ if(dropzone.classList.contains('error')) dropzone.classList.remove('error'); }, 500);
  }

  function escapeHtml(s){
    return s.replace(/[&<>"']/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  var ALLOWED_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  var ALLOWED_EXT = /\.(pdf|docx|txt)$/i;

  function validateAndSet(file){
    if(!file){ showIdle(); return; }
    if(ALLOWED_TYPES.indexOf(file.type) === -1 && !ALLOWED_EXT.test(file.name)){
      showError('Not a PDF, DOCX, or TXT — try again');
      return;
    }
    if(file.size > MAX_BYTES){
      showError('File over 10mb');
      return;
    }
    showFile(file);
  }

  dropzone.addEventListener('click', function(){ fileInput.click(); });
  dropzone.addEventListener('keydown', function(e){
    if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); fileInput.click(); }
  });

  ['dragenter','dragover'].forEach(function(evt){
    dropzone.addEventListener(evt, function(e){
      e.preventDefault(); e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });
  ['dragleave','drop'].forEach(function(evt){
    dropzone.addEventListener(evt, function(e){
      e.preventDefault(); e.stopPropagation();
      if(evt === 'dragleave' && e.target !== dropzone) return;
      dropzone.classList.remove('dragover');
    });
  });
  dropzone.addEventListener('drop', function(e){
    var files = e.dataTransfer.files;
    if(files && files.length){
      fileInput.files = files;
      validateAndSet(files[0]);
    }
  });
  fileInput.addEventListener('change', function(){
    validateAndSet(fileInput.files[0]);
  });

  showIdle();

  /* ---------------- template picker ---------------- */
  var cards = Array.prototype.slice.call(document.querySelectorAll('.tmpl-card'));
  var templateInput = document.getElementById('template-input');

  function selectCard(card){
    cards.forEach(function(c){
      c.classList.remove('selected');
      c.setAttribute('aria-checked','false');
    });
    card.classList.add('selected');
    card.setAttribute('aria-checked','true');
    templateInput.value = card.getAttribute('data-value');
  }

  cards.forEach(function(card){
    card.addEventListener('click', function(){ selectCard(card); });
    card.addEventListener('keydown', function(e){
      if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); selectCard(card); }
    });
  });

  /* ---------------- trace / progress ---------------- */
  var nodes = Array.prototype.slice.call(document.querySelectorAll('.trace-node'));
  var lines = Array.prototype.slice.call(document.querySelectorAll('.trace-line'));
  var packet = document.getElementById('packet');
  var nodePositions = [60,252,444,636,828];

  function lightUpTo(index, state){
    nodes.forEach(function(n){
      var i = parseInt(n.getAttribute('data-node'),10);
      n.classList.remove('done','active','error');
      if(i < index) n.classList.add('done');
      else if(i === index) n.classList.add(state || 'active');
    });
    lines.forEach(function(l){
      var i = parseInt(l.getAttribute('data-line'),10);
      l.classList.remove('done','active');
      if(i < index) l.classList.add('done');
      else if(i === index) l.classList.add('active');
    });
  }

  function movePacket(fromIdx, toIdx, duration, cb){
    if(reduceMotion){ cb && cb(); return; }
    packet.classList.add('moving');
    var start = nodePositions[fromIdx], end = nodePositions[toIdx];
    var t0 = null;
    function step(ts){
      if(!t0) t0 = ts;
      var p = Math.min((ts - t0) / duration, 1);
      packet.setAttribute('cx', start + (end-start)*p);
      if(p < 1) requestAnimationFrame(step);
      else { packet.classList.remove('moving'); cb && cb(); }
    }
    requestAnimationFrame(step);
  }

  /* ---------------- stage readout + submit ---------------- */
  var form = document.getElementById('generate-form');
  var stageReadout = document.getElementById('stage-readout');
  var stageLines = Array.prototype.slice.call(document.querySelectorAll('.stage-line'));
  var btnLabel = document.getElementById('btn-label');

  var STAGE_TIMING = [
    {stage:'extract', node:1, ms:1400},
    {stage:'validate', node:2, ms:1200},
    {stage:'gemini', node:3, ms:5500},
    {stage:'render', node:4, ms:1800}
  ];

  function setStageLine(stage, state){
    stageLines.forEach(function(l){
      if(l.getAttribute('data-stage') === stage){
        l.classList.remove('active','done');
        l.classList.add(state);
        l.querySelector('.mark').textContent = state === 'done' ? '✓' : '▸';
      }
    });
  }

  function runOptimisticProgress(){
    stageReadout.classList.add('visible');
    lightUpTo(0,'done');
    var idx = 0;
    function next(){
      if(idx >= STAGE_TIMING.length) return;
      var s = STAGE_TIMING[idx];
      var prevNode = idx; // node index just completed
      setStageLine(s.stage,'active');
      movePacket(prevNode, s.node, Math.min(s.ms, 900), function(){
        lightUpTo(s.node,'active');
      });
      setTimeout(function(){
        setStageLine(s.stage,'done');
        idx++;
        next();
      }, s.ms);
    }
    next();
  }

  form.addEventListener('submit', function(e){
    e.preventDefault();
    if(generateBtn.disabled) return;

    generateBtn.disabled = true;
    generateBtn.classList.add('loading');
    btnLabel.textContent = 'generating…';
    formStatus.textContent = 'pipeline running — this takes 5–15s';
    formStatus.classList.remove('error');

    runOptimisticProgress();

    var data = new FormData(form);
    fetch(form.action, { method: 'POST', body: data })
      .then(function(res){
        lightUpTo(5,'done');
        stageLines.forEach(function(l){ setStageLine(l.getAttribute('data-stage'),'done'); });
        if(res.redirected){
          window.location = res.url;
          return;
        }
        return res.text().then(function(html){
          document.open();
          document.write(html);
          document.close();
        });
      })
      .catch(function(){
        var activeNode = nodes.find(function(n){ return n.classList.contains('active'); });
        var idx = activeNode ? parseInt(activeNode.getAttribute('data-node'),10) : 1;
        lightUpTo(idx,'error');
        generateBtn.disabled = false;
        generateBtn.classList.remove('loading');
        btnLabel.textContent = 'generate portfolio';
        formStatus.textContent = 'generation failed — check file and retry';
        formStatus.classList.add('error');
      });
  });

})();