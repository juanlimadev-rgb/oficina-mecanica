// A mesma proteção atende formulários Flask e chamadas JSON das telas existentes.
const nativeFetch = window.fetch.bind(window);
window.fetch = (input, options = {}) => {
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    const method = (options.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    if (url.origin === location.origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        const headers = new Headers(options.headers || (input instanceof Request ? input.headers : undefined));
        headers.set('X-CSRF-Token', document.querySelector('meta[name="csrf-token"]').content);
        options = { ...options, headers };
    }
    return nativeFetch(input, options);
};
function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
}
