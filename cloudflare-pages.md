# Cloudflare Workers + Astro (актуальный UI)

Вы создали проект через **Workers → шаблон Astro**. Это **Workers Builds**, не старый Pages.

Документация: [Workers Builds configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)

## Где настраивать

1. [dash.cloudflare.com](https://dash.cloudflare.com)
2. Слева: **Workers & Pages**
3. Клик по **имени вашего приложения** (Worker, URL вида `*.workers.dev`)
4. Вверху вкладка **Settings**
5. В левом меню Settings: **Build**

Там два поля:

| Поле | Значение |
|------|----------|
| **Build command** | `npm ci && npm run build` |
| **Deploy command** | `npx wrangler deploy --assets ./dist --name casinoexpert-de1 --compatibility-date 2024-07-01` |

**Не** `npm run deploy`, если в GitHub нет этого скрипта.  
Либо Deploy command = `npm run deploy`, если в `package.json` есть `"deploy": "wrangler deploy"`.

Нажмите **Save**. Следующий билд подхватит настройки.

## Node.js 22

Settings → **Build** → блок **Build variables and secrets** (или Environment variables для build):

- `NODE_VERSION` = `22`

## Запуск деплоя

1. Вкладка **Deployments** (или **Overview** → список деплоев)
2. **Retry deployment** / новый push в GitHub

## Успешный лог

```
310 page(s) built
Success: Build command completed
... wrangler deploy ...
Success
```

## Домен

Settings → **Domains & Routes** → **Add** → **Custom domain** → `onlinecasinoexperte.org`

## Проверка

- `https://<имя>.workers.dev/site-build-id.txt`
- потом `https://onlinecasinoexperte.org/`

## wrangler.toml в GitHub

Для Workers static site нужно:

```toml
[assets]
directory = "./dist"
```

**Ошибка `dist/_worker.js/index.js was not found`:** в GitHub остался `wrangler.jsonc` от шаблона Astro (SSR). Удалите его. Нужен только `wrangler.toml` с `[assets] directory = "./dist"`.
