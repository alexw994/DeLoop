import {createRouter, createWebHistory} from 'vue-router'
import {getUser} from '@/utils'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: () => import("views/Home.vue"),
        redirect: '/projects',
        children: [
            {
                path: '/dashboard',
                name: 'Dashboard',
                component: () => import("views/Dashboard.vue")
            },
            {
                path: '/datasets',
                name: 'Datasets',
                component: () => import("views/dataset/Dataset.vue")
            },
            {
                path: '/labeling',
                name: 'Labeling',
                component: () => import("views/dataset/Labeling.vue")
            },
            {
                path: '/data?project_name=:project_name',
                name: 'project records',
                component: () => import("views/records/DataRecords.vue")
            },
            {
                path: '/data',
                name: 'Data Records',
                component: () => import("views/records/DataRecords.vue")
            },
            {
                path: '/projects',
                name: 'Projects',
                component: () => import('views/project/Project.vue')
            },
            {
                path: '/projects/new',
                name: 'create a Project',
                component: () => import('views/project/ProjectNew.vue')
            },
            {
                path: '/404',
                name: '404',
                component: () => import('views/others/404.vue')
            },
            {
                path: '/:pathMatch(.*)',
                redirect: '/404'
            }
        ]
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import("views/auth/Login.vue")
    }
]

const router = createRouter({
    history: createWebHistory(import.meta.env.DELOOP_BASE),
    routes
})

router.beforeEach((to, from, next) => {
    let isAuthenticated = false;
    let user = getUser();
    if (user && user.name) {
        isAuthenticated = true;
    }

    if (!isAuthenticated && to.name !== 'Login' && to.name !== 'OAuth') next({name: 'Login'})
    else if (isAuthenticated && (to.name == 'Login' || to.name == 'OAuth')) next({name: 'Home'})
    else next()
})

export default router