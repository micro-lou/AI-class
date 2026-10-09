import userApi from '@/api/user'
import store from '@/store'

import {Cell,SwipeCell, Popup, Button , Sidebar, SidebarItem , CellGroup, Col, Icon, Row, Tabbar, TabbarItem, Toast,Dialog} from 'vant';
import menuConfig from "@/view/config";
import { debounce } from 'lodash'
export default {
    components: {
        [Row.name]: Row,
        [Col.name]: Col,
        [Icon.name]: Icon,
        [Cell.name]: Cell,
        [CellGroup.name]: CellGroup,
        [Tabbar.name]: Tabbar,
        [TabbarItem.name]: TabbarItem,
        [Toast.name]: Toast,
        [Dialog.name]: Dialog,
        [SwipeCell.name]: SwipeCell,
        [Popup.name]: Popup,
        [Button.name]: Button,
        [Sidebar.name]: Sidebar,
        [SidebarItem.name]: SidebarItem
},
    data() {
        return {
            store:store,
            menuConfig: this.setMenu(),
            activeMenu: 0,
            menuCollapsed: true,
            isMobile: false,
            screenWidth: 0,
            mobileMenuStyle: {
                position: 'fixed',
                left: '-220px',
                top: '0',
                height: '100vh',
                zIndex: '1000',
                transition: 'left 0.3s'
            }
        }
    },
    created() {
        this.screenWidth = window.innerWidth
        this.checkIsMobile()
        window.addEventListener('resize', debounce(this.onResize, 200))

        // 初始化激活菜单
        this.setActiveMenu()
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.onResize)
    },
    watch: {
        $route() {
            this.setActiveMenu()
        }
    },
    methods: {
        setMenu(){
            store.menuConfig=this.processMenuConfig(menuConfig)
            return store.menuConfig;
        },
        processMenuConfig(config) {
            console.log("processMenuConfig.......:",localStorage.getItem("userInfo"))
            var userInfo=JSON.parse(localStorage.getItem("userInfo"))
            console.log("userInfo",userInfo)
            if(userInfo==null||userInfo.roleType==1||userInfo.roleType==2){
                config=[{
                    title: '首页',
                    icon: 'home-o',
                    path: '/rankingList'
                },
                    {
                        title: '个人中心',
                        icon: 'user-o',
                        path: '/user',
                    },
                    {
                        title: '退出登录',
                        icon: 'guide-o',
                        path: '/login',
                    }]
            }
            return config.map(item => {
                return {
                    ...item,
                    expanded: false
                }
            })
        },
        setActiveMenu() {
            const currentPath = this.$route.path
            this.menuConfig.forEach((item, index) => {
                if (item.path === currentPath) {
                    this.activeMenu = index
                } else if (item.children) {
                    const childIndex = item.children.findIndex(child => child.path === currentPath)
                    if (childIndex !== -1) {
                        this.activeMenu = index
                        this.$set(item, 'expanded', true)
                    }
                }
            })
        },
        handleMenuClick(item) {
            this.$set(item, 'expanded', !item.expanded)
            this.toggleMenu()
            if (item.children && item.children.length) {
                // 有子菜单则展开/收起
                this.$set(item, 'expanded', !item.expanded)
            } else if (item.path) {
                const isSameRoute = this.$route.path === item.path

                if (!isSameRoute) {
                    this.$router.push(item.path)
                }
            }
        },
        handleSubmenuClick(item) {
            this.$router.push(item.path)
            if (this.isMobile) {
                this.menuCollapsed = true
            }
        },
        toggleMenu() {
            this.menuCollapsed = !this.menuCollapsed
            this.mobileMenuStyle.left = this.menuCollapsed ? '-220px' : '0'
        },
        onResize() {
            this.screenWidth = window.innerWidth
            this.checkIsMobile()
        },
        checkIsMobile() {
            this.isMobile = this.screenWidth < 768
            if (!this.isMobile) {
                this.menuCollapsed = false
            }
        }
    }
}
