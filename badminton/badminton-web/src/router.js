import Vue from 'vue'
import Router from 'vue-router'
import store from '@/store'
import storage from '@/utils/storage'
Vue.use(Router)

const routes = [
    {
        path: '*',
        redirect: '/user',
        meta: {
            requiresLayout: true, // 标记需要布局
            requireAuth: true,
        }
    },
    {
        name: 'error',
        component: () => import('./view/common/error'),
        meta: {
            requireAuth: true,
            title: '系统异常',
            requiresLayout: true // 标记需要布局
        }
    },
    {
        name: 'login',
        component: () => import('./view/login'),
        meta: {
            title: '登录',
            noLayout: true, // 标记不需要布局
        }
    },

    {
        name: 'user',
        component: () => import('./view/user'),
        meta: {
            requireAuth: true,
            title: '首页',
            requiresLayout: true // 标记需要布局
        }
    },
    {
        name: 'setting',
        component: () => import('./view/setting'),
        meta: {
            requireAuth: true,
            title: '设置',
            requiresLayout: true // 标记需要布局
        }
    },
    {
        name: 'updateUserName',
        component: () => import('./view/setting/updateUserName'),
        meta: {
            requireAuth: true,
            title: '修改姓名',
            requiresLayout: true // 标记需要布局
        }
    },
    {
        name: 'updateMobile',
        component: () => import('./view/setting/updateMobile'),
        meta: {
            requireAuth: true,
            title: '修改手机号',
            requiresLayout: true // 标记需要布局
        }
    },
    {
        name: 'updatePwd',
        component: () => import('./view/setting/updatePwd'),
        meta: {
            requireAuth: true,
            title: '修改密码',
            requiresLayout: true // 标记需要布局
        }
    },
    {
        name: 'avatar',
        component: () => import('./view/setting/avatar'),
        meta: {
            requireAuth: true,
            title: '修改头像',
            requiresLayout: true // 标记需要布局
        }
    },

    {
        name: 'userList',
        component: () => import('./view/userList'),
        meta: {
            requireAuth: true,
            title: '人员管理',
            requiresLayout: true // 标记需要布局
        }
    },

    {
        name: 'createUser',
        component: () => import('./view/createUser'),
        meta: {
            requireAuth: true,
            title: '人员管理',
            requiresLayout: true // 标记需要布局
        }
    },

    {
        name: 'rankingList',
        component: () => import('./view/rankingList'),
        meta: {
            requireAuth: true,
            title: '积分排名',
            requiresLayout: true // 标记需要布局
        }
    }

]

routes.forEach(route => {
    route.path = route.path || '/' + (route.name || '');
})

const router = new Router({routes})

router.beforeEach((to, from, next) => {
    const title = to.meta && to.meta.title
    if (title) {
        document.title = title;
    }
    // 判断该路由是否需要登录权限
    if (to.meta.requireAuth) {
        if(storage.getToken()){
            next();
        } else {
            next({
                path: '/login',
                query: {redirect: to.fullPath}  // 将跳转的路由path作为参数，登录成功后跳转到该路由
            })
        }
    } else {
        next()
    }
})


export {
    router
}
