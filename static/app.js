// Utilitário usado pelas telas existentes.
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
}

// A busca existe apenas na tela Nova OS. Não interromper scripts de outras telas.
(() => {
    const search = document.getElementById('busca-cliente');
    const results = document.getElementById('lista-clientes-busca');
    const selected = document.getElementById('cliente_id');
    if (!search || !results || !selected) return;
    let timer;
    let version = 0;
    search.addEventListener('input', () => {
        clearTimeout(timer);
        selected.value = '';
        results.replaceChildren();
        const term = search.value.trim();
        const requestVersion = ++version;
        if (term.length < 2) return;
        timer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/clientes?busca=${encodeURIComponent(term)}`);
                if (!response.ok) throw new Error('Não foi possível consultar os clientes.');
                const customers = await response.json();
                if (requestVersion !== version) return;
                results.replaceChildren();
                for (const customer of customers) {
                    const option = document.createElement('button');
                    option.type = 'button';
                    option.className = 'cliente-item';
                    const name = document.createElement('strong');
                    name.textContent = customer.nome;
                    const details = document.createElement('span');
                    details.textContent = `${customer.moto || '-'} · ${customer.placa || '-'} · ${customer.telefone || '-'}`;
                    option.append(name, document.createElement('br'), details);
                    option.addEventListener('click', () => {
                        selected.value = customer.id;
                        search.value = customer.nome;
                        results.replaceChildren();
                        ++version;
                    });
                    results.appendChild(option);
                }
            } catch (error) {
                if (requestVersion === version) results.textContent = error.message;
            }
        }, 250);
    });
})();
