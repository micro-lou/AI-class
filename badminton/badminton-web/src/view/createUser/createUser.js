import userApi from '@/api/users'
import { NavBar, Form, Field, Button, Toast, Picker, Popup } from 'vant'

export default {
    components: {
        [NavBar.name]: NavBar,
        [Form.name]: Form,
        [Field.name]: Field,
        [Button.name]: Button,
        [Picker.name]: Picker,
        [Popup.name]: Popup
    },
    data() {
        return {
            formData: {
                userName: '',
                playerName: '',
                password: '123456', // 默认密码
                gender: '男',
                initialPoints: 1000,
                currentPoints: 1000,
                roleType: 1,
                roleTypeText: '选手',
                salt:''
            },
            showGenderPicker: false,
            showRoleTypePicker: false,
            genderOptions: ['男', '女'],
            roleTypeOptions: [
                { text: '选手', value: 1 },
                { text: '裁判', value: 2 },
                { text: '管理员', value: 3 }
            ],


        }
    },
    methods: {
        // 返回上一页
        onBack() {
            this.$router.go(-1)
        },

        // 性别选择确认
        onGenderConfirm(value) {
            this.formData.gender =value;
            this.showGenderPicker = false
        },



        onRoleTypeConfirm(value){
            this.showRoleTypePicker = false;
            this.formData.roleType = value.value;
            this.formData.roleTypeText = value.text
        },

        onGenerateSalt() {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            const array = new Uint8Array(5);
            window.crypto.getRandomValues(array);

            let salt = '';
            array.forEach(byte => {
                salt += chars[byte % chars.length];
            });

            this.formData.salt = salt;
        },



        // 表单提交
        handleSubmit() {
            this.onGenerateSalt();
            userApi.createUser({
                userName: this.formData.userName,
                playerName: this.formData.playerName,
                // password: this.formData.password,
                gender: this.formData.gender,
                initialPoints: this.formData.initialPoints,
                currentPoints: this.formData.currentPoints,
                roleType: this.formData.roleType,
                salt: this.formData.salt,
            }).then(() => {
                Toast.success('新增用户成功')
                this.$router.push('/user/list') // 返回列表页
            }).catch(err => {
                Toast.fail((err.response && err.response.data && err.response.data.message) || '新增用户失败')
            })
        }
    }
}