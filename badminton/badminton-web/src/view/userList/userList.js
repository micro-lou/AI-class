import userApi from '@/api/users'
import {
    Cell,
    CellGroup,
    Col,
    Icon,
    Field,
    Row,
    NavBar,
    Form,
    Popup,
    Tabbar,
    TabbarItem,
    Toast,
    Dialog,
    SwipeCell,
    List,
    PullRefresh,
    Tag,
    Search,
    Button,
    Picker
} from 'vant'

export default {
    components: {
        [Row.name]: Row,
        [Col.name]: Col,
        [Icon.name]: Icon,
        [SwipeCell.name]: SwipeCell,
        [Cell.name]: Cell,
        [CellGroup.name]: CellGroup,
        [Tabbar.name]: Tabbar,
        [TabbarItem.name]: TabbarItem,
        [Toast.name]: Toast,
        [Dialog.name]: Dialog,
        [List.name]: List,
        [PullRefresh.name]: PullRefresh,
        [Tag.name]: Tag,
        [Search.name]: Search,
        [Button.name]: Button,
        [Popup.name]: Popup,
        [Form.name]: Form,
        [Field.name]: Field,
        [Picker.name]: Picker,
        [NavBar.name]: NavBar

    },
    data() {
        return {
            page:1,
            limit:10,
            activeFooter: 0,
            userList: [],          // 用户列表数据
            loading: false,        // 加载状态
            finished: false,       // 是否加载完成
            refreshing: false, // 下拉刷新状态
            searchKeyword: '',     // 搜索关键词
            showEdit: false,  // 显示添加用户弹窗
            editForm: {
                id:'',
                userName: '',
                playerName: '',
                password: '', // 默认密码
                gender: '男',
                initialPoints: 1000,
                currentPoints: 1000,
                roleType: 1,
                roleTypeText: '选手'
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
    mounted() {
        this.init()
    },
    methods: {

        goToCreateUser() {
            this.$router.push('/createUser')
        },

        init() {
            this.loadUserList(true)
        },

        // 加载用户列表
        loadUserList(reset = false) {
            this.loading = true
            userApi.getUserList( this.searchKeyword,'page='+this.page+'&limit='+this.limit).then(response => {
                const data = response.data.records || []
                if(this.page==1){
                    this.userList = []
                }
                this.userList.push(...data)
                console.log(" this.userList", this.userList)
                if ( this.userList.length >= response.data.total) {
                    this.finished = true
                }
                this.page++

            }).catch(err => {
                Toast.fail('加载用户列表失败')
                console.error('加载用户列表失败:', err)
            }).finally(() => {
                this.loading = false
                this.refreshing = false
            })
        },

        // 下拉刷新
        onRefresh() {
            this.refreshing = true
            this.page++
            console.log("this.page",this.page)
            this.loadUserList(true)
        },

        // 滚动加载
        onLoad() {
            this.loadUserList()
        },

        // 搜索用户
        onSearch() {
            this.page=1
            this.loadUserList(true)
        },


        // 删除用户
        deleteUser(id) {
            Dialog.confirm({
                title: '确认删除',
                message: '确定要删除该用户吗？'
            }).then(() => {
                userApi.deleteUser(id).then(() => {
                    Toast.success('删除成功')
                    this.loadUserList(true)
                }).catch(() => {
                    Toast.fail('删除失败')
                })
            }).catch(() => {
                // 取消删除
            })

        },

        // 获取角色类型文本
        getRoleTypeText(roleType) {
            const roleMap = {
                1: '选手',
                2: '裁判',
                3: '管理员'
            }
            return roleMap[roleType] || '未知'
        },

        // 获取角色类型标签样式
        getRoleTypeTag(roleType) {
            const typeMap = {
                1: 'primary',
                2: 'success',
                3: 'warning'
            }
            return typeMap[roleType] || 'default'
        },

        // 显示用户详情
        showUserDetail(user) {
            // 构建自定义HTML内容
            const dialogContent = `
              <div class="user-detail-container">
                <!-- 详细信息列表 -->
                <ul class="user-info-list">
                  <li class="info-item">
                    <span class="info-label">用户名</span>
                    <span class="info-value">${user.userName}</span>
                  </li>
                   <li class="info-item">
                    <span class="info-label">选手名</span>
                    <span class="info-value">${user.playerName}</span>
                  </li>
                  <li class="info-item">
                    <span class="info-label">性别</span>
                    <span class="info-value">${user.gender || '未设置'}</span>
                  </li>
                  <li class="info-item">
                    <span class="info-label">当前积分</span>
                    <span class="info-value score">${user.currentPoints || 0}</span>
                  </li>
                  <li class="info-item">
                    <span class="info-label">角色</span>
                    <span class="info-value">${this.getRoleTypeText(user.roleType)}</span>
                  </li>
                  <!-- 可以添加更多信息项 -->
                </ul>
              </div>
            `;

            // 引入样式（通过style标签注入）
            const style = `
              <style>
               .user-detail-container {
                  padding: 16px 0;
                }
                .user-info-list {
                  list-style: none;
                  padding: 0 16px;
                  margin: 0;
                  margin-block-start: -10em;
                  margin-block-end: -8em;
                }
                .info-item {
                  display: flex;
                  padding: 10px 0;
                }
                .info-item:last-child {
                  border-bottom: none;
                }
                .info-label {
                  width: 80px;
                  color: #888;
                  font-size: 14px;
                }
                .info-value {
                  flex: 1;
                  font-size: 14px;
                }
                .score {
                  color: #4a71ff;
                  font-weight: bold;
                }
              </style>
            `;
            Dialog.alert({
                title: '用户详情',
                message:style + dialogContent,
            })
        },

        onGenderConfirm(value) {
            this.editForm.gender =value;
            this.showGenderPicker = false
        },



        onRoleTypeConfirm(value){
            this.showRoleTypePicker = false;
            this.editForm.roleType = value.value;
            this.editForm.roleTypeText = value.text
        },


        initEditForm(user) {
            this.editForm = {
                id: user.id,
                userName: user.userName,
                playerName: user.playerName || '',
                password: '',
                gender: user.gender,
                currentPoints: user.currentPoints,
                roleType: user.roleType,
                roleTypeText: this.getRoleTypeText(user.roleType)
            }
            this.showEdit = true
            console.log("this.editForm",this.editForm)
        },

        // 编辑当前用户
        async editCurrentUser() {
            try {
                const params = {
                     userName: this.editForm.userName,
                    playerName: this.editForm.playerName,
                    gender: this.editForm.gender,
                    currentPoints: this.editForm.currentPoints,
                    roleType: this.editForm.roleType
                }

                // 如果有密码修改才传密码
                if (this.editForm.password) {
                    params.password = this.editForm.password
                }

                await userApi.updateUser(this.editForm)
                this.$toast.success('修改成功')
                this.showEdit = false
                this.loadUserList(true) // 刷新列表
            } catch (error) {
                console.error('修改用户失败:', error)
                this.$toast.fail('修改失败')
            }
        }
    }
}
