import "@testing-library/jest-dom";

// Client ID fake só pra permitir que o GoogleLoginButton renderize
// nos testes (sem ele o componente retorna null). Nenhuma chamada
// real ao Google acontece nos testes.
process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID = "test-google-client-id";
