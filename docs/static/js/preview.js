document.addEventListener('submit', event => {
          const form = event.target;
          if (form.matches('[data-preview]')) {
            event.preventDefault(); event.stopImmediatePropagation(); return;
          }
          if (form.querySelector('[name="q"]')) {
            event.preventDefault();
            const query = form.querySelector('[name="q"]').value;
            location.href = 'amigos.html?q=' + encodeURIComponent(query);
          }
        }, true);
        const query = new URLSearchParams(location.search).get('q') || '';
        const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
        document.querySelectorAll('[name="q"]').forEach(input => { input.value = query; });
        const cards = [...document.querySelectorAll('.person-card')];
        if (cards.length && query) {
          cards.forEach(card => { card.hidden = !normalize(card.dataset.search || card.textContent).includes(normalize(query)); });
          if (cards.every(card => card.hidden)) {
            const empty = document.createElement('p'); empty.className = 'preview-empty';
            empty.textContent = 'Nenhuma garagem de exemplo encontrada. Tente outro nome, cidade ou carro.';
            document.querySelector('.people-grid').append(empty);
          }
        }
        