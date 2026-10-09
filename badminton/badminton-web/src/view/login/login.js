import loginApi from '@/api/login'
import store from '@/store'
import storage  from '@/utils/storage'
import AesUtil from '@/utils/aes'
import menuConfig from "@/view/config";
import { Row, Col, Icon, Cell, CellGroup,Field,Button,Toast,
    Tabbar,
    TabbarItem,Dialog} from 'vant';

export default {
    components: {
        [Row.name]: Row,
        [Col.name]: Col,
        [Icon.name]: Icon,
        [Cell.name]: Cell,
        [CellGroup.name]: CellGroup,
        [Tabbar.name]: Tabbar,
        [TabbarItem.name]: TabbarItem,
        [Field.name]: Field,
        [Button.name]: Button,
        [Toast.name]: Toast,
        [Dialog.name]: Dialog
    },
    data() {
        return {
            mobile:'',
            smsCode:'',
            password:'',
            activeFooter:3,
            show1:false,
            show2:true,
            redirect:'',
            hasSendSms: false,
            second: 60
        }
    },
    mounted(){
      this.init()
    },
    methods:{
        init(){
            if(store.state.app.user.nickName){
                this.$router.push({path: '/user'})
                return
            }
            if(this.$route.query.redirect){
                this.redirect = this.$route.query.redirect
            }
        },
        toLoginByPassword(){
            this.show1 = false;
            this.show2 = true;
        },
        toRegister(){
            this.show2 = false;
            this.show1 = true;
        },
        resetForLogin(){
            //登录成功后初始化数据状态
            //清空缓存中的地址信息
            storage.set('chosenAddressId','')
        },
        loginOrRegister(){
            loginApi.loginOrReg(this.mobile,this.smsCode).then( response=> {
                store.dispatch('app/toggleToken',response.data.token)
                store.dispatch('app/toggleUser',response.data.user)
                if(response.data.initPassword){
                    Toast({duration:8000,message:'欢迎新用户，请谨慎保管您的初始密码：'+response.data.initPassword})
                }
                this.resetForLogin()
                if(this.redirect){
                    this.$router.push({path: this.redirect})
                }else {
                    this.$router.push({path: '/user'})
                }
            }).then( (err) => {
                // Toast.fail(err)
            })
        },
        loginByPass(){
            loginApi.loginByPassword(this.mobile, AesUtil.encrypt(this.password)).then( response=> {
                store.dispatch('app/toggleToken',response.data.token)
                store.dispatch('app/toggleUser',response.data.user)
                this.resetForLogin()
                if(this.redirect){
                   this.$router.push({path: this.redirect})
                }else {
                   this.$router.push({path: '/rankingList'})
                    console.log("userInfo",response.data.user)
                    localStorage.setItem("userInfo",JSON.stringify(response.data.user))
                    console.log("userInfo1", localStorage.getItem("userInfo"))
                    store.menuConfig=this.processMenuConfig(menuConfig)

                }
            }).catch( err=>{
                Toast(err)
            })
        },
        sendSms(){
            this.hasSendSms = true
            loginApi.sendSmsCode(this.mobile).then( response => {
                this.setTimeOut()
            })
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
        setTimeOut () {
            let timer = setTimeout(() => {
                this.setTimeOut()
                if(this.second > 0) {
                    this.second--
                }
            }, 1000)
            if(this.second <= 0) {
                this.hasSendSms = false
                this.second = 60
                clearTimeout(timer)
            }
        }
    }
};
