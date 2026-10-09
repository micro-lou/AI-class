import request from '@/utils/request'

export default {
    // 获取用户列表（分页+搜索）
    getUserList: function(keyword,param) {
        return request({
            url: '/users?'+param,
            method: 'get',
            params: {
                keyword: keyword
            }
        })
    },

    // 创建用户
    createUser: function(userData) {
        return request({
            url: '/users',
            method: 'post',
            data: userData
        })
    },

    // 获取用户详情
    getUserDetail: function(userId) {
        return request({
            url: '/users/' + userId,
            method: 'get'
        })
    },

    // 更新用户信息
   updateUser: function (data) {
        return request({
            url: '/users/update',
            method: 'post',
            data
        })
    },

    // 删除用户
    deleteUser: function(id) {
        return request({
            url: '/users/' + id,
            method: 'delete'
        })
    },

    // 获取选手排行榜
    getPlayerRanking: function() {
        return request({
            url: '/users/ranking',
            method: 'get'
        })
    },

    // 更新用户积分
    updateUserPoints: function(userId, points) {
        return request({
            url: '/users/' + userId + '/points',
            method: 'put',
            params: {
                points: points
            }
        })
    },

    // 检查用户名是否可用
    checkUsernameAvailable: function(username) {
        return request({
            url: '/users/checkUsername',
            method: 'get',
            params: {
                username: username
            }
        })
    },

    // 检查选手名是否可用
    checkPlayerNameAvailable: function(playerName) {
        return request({
            url: '/users/checkPlayerName',
            method: 'get',
            params: {
                playerName: playerName
            }
        })
    },

    // 获取所有裁判
    getAllReferees: function() {
        return request({
            url: '/users/referees',
            method: 'get'
        })
    },
    getAllPlayers: function() {
        return request({
            url: '/users/players',
            method: 'get'
        })
    },

    // 上传用户头像
    uploadAvatar: function(file) {
        return request({
            url: '/file/upload/avatar',
            method: 'post',
            data: file,
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
    }
}