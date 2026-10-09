import rankingApi from '@/api/ranking'
import usersApi from '@/api/users'
import {
    NavBar,
    List,
    Cell,
    Image as VanImage,
    Popup,
    Divider,
    CellGroup,
    PullRefresh,
    Toast,
    Tab,
    Tabs,
    Tag,
    Button,
    Dialog,
    SwipeCell,
    Field,
    Picker,
    DatetimePicker
} from 'vant'
import {formatter} from "@vue/cli-service/lib/util/resolveLoaderError";

export default {
    components: {
        [NavBar.name]: NavBar,
        [List.name]: List,
        [Cell.name]: Cell,
        [VanImage.name]: VanImage,
        [Popup.name]: Popup,
        [Divider.name]: Divider,
        [CellGroup.name]: CellGroup,
        [PullRefresh.name]: PullRefresh,
        [Tab.name]: Tab,
        [Tag.name]: Tag,
        [Button.name]: Button,
        [Dialog.name]: Dialog,
        [Tabs.name]: Tabs,
        [SwipeCell.name]: SwipeCell,
        [Field.name]: Field,
        [Picker.name]: Picker,
        [DatetimePicker.name]: DatetimePicker
    },
    data() {
        const now = new Date()
        now.setMinutes(0, 0, 0)
        return {
            page: 1,
            matchesPage: 1,
            limit: 10,
            rankingList: [],
            loading: false,
            matchesLoading: false,
            finished: false,
            matchesFinished: false,
            refreshing: false,
            matchesRefreshing: false,
            showPlayerDetail: false,
            addPlayers:false,
            showMatchDetail: false,
            currentPlayer: null,
            currentMatch: null,
            matchesList: [],
            active: 0,
            total: 0,
            matchesTotal: 0,
            showDetail: false,
            showAddMatchPopup: false,
            showTimePicker: false,
            showMatchTypePicker: false,
            showRefereePicker : false,
            showRed1Picker: false,
            showRed2Picker: false,
            showBlue1Picker: false,
            showBlue2Picker: false,
            currentDate: now,
            minDate: new Date(2020, 0, 1),
            maxDate: new Date(now.getFullYear() + 1, 11, 31),
            matchForm: {
                matchType: '单打',
                matchTime: this.formatDateTime(now),
                red_1: null,
                red_2: null,
                blue_1: null,
                blue_2: null,
                refereeName: '',
                redPoints: 0,
                bluePoints: 0,
                isValid: 0
            },
            matchTypeOption: ['单打', '双打'],
            refereeOptions: [],
            playerOptions: [],
            formRules: {
                matchType: [{required: true, message: '请选择比赛类型'}],
                matchTime: [{required: true, message: '请选择比赛时间'}],
                red_1: [{required: true, message: '请选择红方选手'}],
                blue_1: [{required: true, message: '请选择蓝方选手'}],
                refereeName: [{required: true, message: '请选择裁判'}],
                redPoints: [{required: true, validator: this.validatePoints}],
                bluePoints: [{required: true, validator: this.validatePoints}]
            },
            // 用 require 处理路径，确保打包后能正确找到图片
            tabBackgrounds: [
                `url(${require('@/assets/img/bg.png')})`,   // 推荐用 @ 表示 src 目录
                `url(${require('@/assets/img/bg1.png')})`
            ],
            // 默认背景也用 require 处理
            tabBackground: `url(${require('@/assets/img/bg.png')})`
        }
    },
    methods: {
        // 在方法中处理文本
        formatTextWithSpace(text) {
            if (text.length === 2) {
                // 两个字中间加空格（使用中文全角空格，更美观）
                return text.charAt(0) + '　' + text.charAt(1);
            }
            return text; // 三个字或其他长度保持不变
        },
        // 获取排名列表
        fetchRankingList(reset = false) {
            this.loading = true
            rankingApi.getRankingList(this.page, this.limit).then(response => {
                const data = response.data.records || []
                if (this.page == 1) {
                    this.rankingList = []
                }
                this.rankingList.push(...data)
                if (this.rankingList.length >= response.data.total) {
                    this.finished = true
                }
                this.page++
                this.loading = false
                this.refreshing = false
            }).catch(error => {
                Toast.fail('获取排名数据失败')
                this.loading = false
                this.refreshing = false
            })
        },
        // 加载更多
        onLoad() {
            if (this.active == 0) {
                this.changeTab()
            }
        },
        changeTab() {
            var userInfo=JSON.parse( localStorage.getItem("userInfo"))
            if(userInfo.roleType!=1){
                this.addPlayers=true
            }else{
                this.addPlayers=false
            }

            console.log("active", this.active)
            if (this.active == 0 && !this.finished) {
                this.fetchRankingList()
            }
            if (this.active == 1 && !this.matchesFinished) {
                this.fetchMatchesList()
            }
            this.tabBackground = this.tabBackgrounds[this.active]
        },
        // 下拉刷新
        onRefresh() {

            if (this.active == 0) {
                this.refreshing = true
            }
            if (this.active == 1) {
                this.matchesRefreshing = true
            }
            // this.changeTab()
        },

        // 显示选手详情
        getPlayerDetail(id) {
            rankingApi.getPlayerStats(id).then(response => {
                this.currentPlayer = response.data
                this.showPlayerDetail = true
            }).catch(error => {
                Toast.fail('获取选手详情失败')
            })
        },

        // 获取比赛列表
        fetchMatchesList(reset = false) {
            console.log("fetchMatchesList")
            this.loading = true
            if (reset) {
                this.matchesPage = 1
                this.matchesFinished = false
            }

            rankingApi.getMatchesList(this.matchesPage, this.limit).then(response => {
                const data = response.data.records || response.data
                if (this.matchesPage === 1) {
                    this.matchesList = []
                }
                this.matchesList.push(...data)
                console.log("matchesList", this.matchesList)
                this.matchesTotal = response.data.total || data.length

                if (this.matchesList.length >= this.matchesTotal) {
                    this.matchesFinished = true
                }
                this.matchesPage++
                this.matchesLoading = false
                this.matchesRefreshing = false
            }).catch(error => {
                Toast.fail('获取比赛数据失败')
                this.matchesLoading = false
                this.matchesRefreshing = false
            })
        },


        // 删除比赛
        handleDelete(matchId) {
            Dialog.confirm({
                title: '确认删除',
                message: '确定要删除这场比赛记录吗？'
            }).then(() => {
                rankingApi.deleteMatch(matchId).then(() => {
                    Toast.success('删除成功')
                    this.fetchMatchesList(true)
                }).catch(() => {
                    Toast.fail('删除失败')
                })
            }).catch(() => {
                // 取消操作
            })
        },

        // 格式化比赛信息
        formatMatchInfo(match) {
            return `${match.matchType} | ${this.formatDateTime(match.matchTime)} | ${match.redPoints}:${match.bluePoints}`
        },


        // 提交新增比赛表单
        submitMatchForm() {
            rankingApi.createMatch({
                matchType: this.matchForm.matchType,
                matchTime: this.matchForm.matchTime,
                red_1: this.matchForm.red_1,
                red_2: this.matchForm.red_2,
                blue_1: this.matchForm.blue_1,
                blue_2: this.matchForm.blue_2,
                refereeName: this.matchForm.refereeName,
                redPoints: this.matchForm.redPoints,
                bluePoints: this.matchForm.bluePoints,

            }).then(() => {
                Toast.success('比赛录入成功')
                this.fetchMatchesList(true)
                this.showAddMatchPopup=false
            }).catch(err => {
                Toast.fail((err.response && err.response.data && err.response.data.message) || '比赛录入失败')
            })
        },


        // 验证比分
        validatePoints(value) {
            if (value === '' || value === null) {
                return '请输入比分'
            }
            if (isNaN(value) || value < 0) {
                return '请输入有效数字'
            }
            return true
        },



        // 重置表单
        resetMatchForm() {
            this.matchForm = {
                matchType: '单打',
                matchTime: '',
                refereeId: null,
                refereeName: '',
                red_1: null,
                red_2: null,
                blue_1: null,
                blue_2: null,
                redPoints: 0,
                bluePoints: 0
            }
        },

        // 裁判选择变化时更新裁判姓名
        handleRefereeChange(refereeName) {
            const selectedReferee = this.refereeOptions.find(r => r.value === refereeName)
            if (selectedReferee) {
                this.matchForm.refereeName = selectedReferee.text
            } else {
                this.matchForm.refereeName = ''
            }
        },

        // 比赛类型变化时处理
        handleMatchTypeChange() {
            if (this.matchForm.matchType === 'singles') {
                this.matchForm.red_2 = null
                this.matchForm.blue_2 = null
            }
        },
        onMatchTypeConfirm(value) {
            this.matchForm.matchType = value;
            this.showMatchTypePicker = false
        },
        // 格式化日期时间为字符串
        formatDateTime(date) {
            if (!date) return ''
            const d = new Date(date)
            const year = d.getFullYear()
            const month = (d.getMonth() + 1).toString().padStart(2, '0')
            const day = d.getDate().toString().padStart(2, '0')
            const hours = d.getHours().toString().padStart(2, '0')
            return `${year}-${month}-${day} ${hours}:00`
        },

        // 时间选择确认
        onTimeConfirm(time) {
            this.matchForm.matchTime = this.formatDateTime(time)
            this.showTimePicker = false
        },

        // 打开新增比赛弹窗时重置时间
        handleAdd() {
            const now = new Date()
            now.setMinutes(0, 0, 0)
            this.currentDate = now
            this.matchForm.matchTime = this.formatDateTime(now)
            this.fetchReferees()
            this.fetchPlayers()
            this.showAddMatchPopup = true

        },
        formatter(type, val) {
            if (type === 'year') {
                return `${val}年`;
            }
            if (type === 'month') {
                return `${val}月`;
            }
            if (type === 'day') {
                return `${val}日`;
            }
            if (type === 'hour') {
                return `${val}时`;
            }
            return val;
        },
        async fetchReferees() {
            try {
                const response = await usersApi.getAllReferees() // 调用获取裁判API
                this.refereeOptions = response.data.map(referee => ({
                    // id: referee.id,
                    name: referee.playerName
                }))
            } catch (error) {
                Toast.fail('获取裁判列表失败')
            }
        },

        // 裁判选择确认
        onRefereeConfirm(referee) {
            // this.matchForm.refereeId = referee.id
            this.matchForm.refereeName = referee.name
            this.showRefereePicker = false
        },

        async fetchPlayers() {
            try {
                const response = await usersApi.getAllPlayers() // 调用获取裁判API
                this.playerOptions = response.data.map(player => ({
                    // id: referee.id,
                    name: player.playerName+ "("+player.userName+")"
                }))
            } catch (error) {
                Toast.fail('获取选手列表失败')
            }
        },

        onRed1Confirm(player) {
            this.matchForm.red_1 = player.name
            this.showRed1Picker = false
        },

        onRed2Confirm(player) {
            this.matchForm.red_2 = player.name
            this.showRed2Picker = false
        },
        onBlue1Confirm(player) {
            this.matchForm.blue_1 = player.name
            this.showBlue1Picker = false
        },
        onBlue2Confirm(player) {
            this.matchForm.blue_2 = player.name
            this.showBlue2Picker = false
        },
        // 根据排名返回对应的背景图片
        getBackgroundImage(rank) {
            // 假设不同排名对应不同图片
            switch(rank) {
                case 1:
                    return require('../../assets/img/first1.png');
                case 2:
                    return require('../../assets/img/second2.png');
                case 3:
                    return require('../../assets/img/third3.png');
                default:
                    // 默认背景图（如果需要）
                    return require('../../assets/img/other.png');
            }
        },
    }




    // getAvatarUrl(gender) {
    //     return gender === '男'
    //         ? require('@/assets/images/male-avatar.png')
    //         : require('@/assets/images/female-avatar.png')
    // }
}
