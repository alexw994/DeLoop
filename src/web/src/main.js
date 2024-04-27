import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import ElTableInfiniteScroll from "el-table-infinite-scroll";
import './styles/index.css'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/notification/style/css'

if (import.meta.env.Deloop_MOCK) {
    import('./mock')
}

const app = createApp(App).use(router).use(createPinia());
app.use(ElTableInfiniteScroll);
app.mount('#app');
