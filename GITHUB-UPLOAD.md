# Как залить на GitHub правильно

Если на https://onlinecasinoexperte.org/ видно **«Hello, Astronaut»** — на GitHub или в Cloudflare **не наш проект**.

## 1. Что должно быть в КОРНЕ репозитория на GitHub

Откройте репозиторий на GitHub. В корне (не во вложенной папке!) должны быть:

```
package.json
astro.config.mjs
src/
public/
scripts/
mirror/
```

**Неправильно** (частая ошибка при загрузке zip):

```
onlinecasinoexperte-astro-git/   ← лишняя папка
  package.json
  src/
```

Если файлы во вложенной папке — в Cloudflare укажите **Root directory** = имя этой папки  
**или** перезалейте содержимое **внутри** папки прямо в корень репозитория.

## 2. Быстрая проверка на GitHub (в браузере)

| Файл | Должно быть | Плохо (шаблон Astro) |
|------|-------------|----------------------|
| `src/pages/index.astro` | `Dein Ratgeber zu Online Casinos` | `Hello, Astronaut` |
| `src/components/Header.astro` | WP-меню из `header.html` | ссылки Home / Blog / About |
| `src/content/blog/` | **нет такой папки** | есть папка с demo-постами |
| `src/pages/` | ~310 файлов `.astro` | 3–5 файлов |

## 3. Проверка после деплоя

Откройте в браузере:

- https://onlinecasinoexperte.org/site-build-id.txt  
  Должно быть: `onlinecasinoexperte-astro-310pages`
- https://onlinecasinoexperte.org/bonus/  
  Должна открыться страница (не 404)

## 4. Cloudflare Pages

| Параметр | Значение |
|----------|----------|
| Build command | `npm ci && npm run build` |
| Build output | `dist` |
| Root directory | *(пусто, если package.json в корне)* |
| Deploy command | **пусто** |
| Node.js | 22 |

В логе успешной сборки должно быть: **`310 page(s) built`**.  
Если **4–10 страниц** — собирается шаблон Astro Blog, не наш сайт.

## 5. Домен

Удаление репозитория на GitHub **не меняет** проект Cloudflare.

1. Cloudflare → **Workers & Pages** → ваш проект → **Custom domains**
2. Убедитесь, что `onlinecasinoexperte.org` привязан к **этому** проекту
3. Если есть **два** проекта — удалите старый или отвяжите домен от него

## 6. Откуда заливать

Локально распакуйте **`archive/onlinecasinoexperte-astro-git.zip`**  
или скопируйте папку **`archive/git-repo/`** — это готовый набор для GitHub.

После любых изменений: `npm run pack-archive`
