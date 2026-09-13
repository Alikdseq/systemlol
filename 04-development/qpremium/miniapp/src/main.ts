import { createApp } from "vue";
import { createPinia } from "pinia";
import { Quasar, Notify, Dialog, Loading } from "quasar";
import quasarLang from "quasar/lang/ru";
import iconSet from "quasar/icon-set/material-icons";
import "@quasar/extras/material-icons/material-icons.css";
import "quasar/src/css/index.sass";
import "./app/styles.css";

import App from "./App.vue";
import { router } from "./app/router";
import { bootTelegramUi } from "./shared/telegram";

bootTelegramUi();

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(Quasar, {
  plugins: { Notify, Dialog, Loading },
  lang: quasarLang,
  iconSet,
});
app.mount("#app");

// Убрать HTML-splash после монтирования Vue
requestAnimationFrame(() => {
  document.getElementById("boot-splash")?.setAttribute("hidden", "");
});
