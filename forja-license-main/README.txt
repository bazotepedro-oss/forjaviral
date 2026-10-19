# Forja Viral — License Server (Zero-Cost)

## 1) Instalar dependências
Dê duplo-clique em `install_deps.bat` (ou rode no CMD).

## 2) Gerar chaves
No CMD (com venv ativa ou depois do install):
```
python generate_keys.py
```
- Guarde `PRIVATE_KEY_B64` só no servidor
- Coloque `PUBLIC_KEY_B64` no seu `license_client.py`

## 3) Configurar e rodar
Edite `start_server.bat` e substitua:
- `REPLACE_ME_PRIVATE_KEY_B64` pela sua PRIVATE_KEY_B64
- `REPLACE_ME_ADMIN_TOKEN` por uma senha forte

Depois rode:
- `start_server.bat`

## 4) Teste rápido
Servidor:
- `POST http://127.0.0.1:8787/check`

## Importante (internet)
Para clientes fora da sua rede:
- Você precisa colocar esse servidor num endereço público (domínio) **ou** abrir a porta 8787 no roteador (port-forward).
