import request from '@/utils/request'

export default {



    // 获取积分排名列表（分页）
    getRankingList(page = 1, limit = 10) {
        return request({
            url: '/ranking/list',
            method: 'get',
            params: {
                page,
                size: limit
            }
        })
    },

    // 搜索选手
    searchPlayers: function(name) {
        return request({
            url: '/ranking/search',
            method: 'get',
            params: {
                name: name
            }
        })
    },

    // 获取选手详情数据
    getPlayerStats: function(id) {
        return request({
            url: '/ranking/player/' + id,
            method: 'get'
        })
    },

    // 更新选手积分 (如果需要)
    updatePlayerPoints: function(playerId, points) {
        return request({
            url: '/ranking/' + playerId + '/points',
            method: 'put',
            params: {
                points: points
            }
        })
    },

    // 获取选手比赛记录 (如果需要)
    getPlayerMatches: function(playerId) {
        return request({
            url: '/ranking/' + playerId + '/matches',
            method: 'get'
        })
    },

    // 获取选手胜负统计 (如果需要)
    getPlayerWinStats: function(playerId) {
        return request({
            url: '/ranking/' + playerId + '/stats',
            method: 'get'
        })
    },



    // 获取比赛列表（分页）
    getMatchesList(page = 1, limit = 10) {
        return request({
            url: '/matches/list',
            method: 'get',
            params: {
                page,
                size: limit
            }
        })
    },

    // 搜索比赛
    searchMatches(keyword) {
        return request({
            url: '/matches/search',
            method: 'get',
            params: {
                keyword
            }
        })
    },

    // 获取比赛详情
    getMatchDetail(id) {
        return request({
            url: `/matches/detail/${id}`,
            method: 'get'
        })
    },

    // 创建比赛
    createMatch(data) {
        return request({
            url: '/ranking/matches',
            method: 'post',
            data
        })
    },

    // 更新比赛
    updateMatch(data) {
        return request({
            url: '/matches/update',
            method: 'put',
            data
        })
    },

    // 删除比赛
    deleteMatch(id) {
        return request({
            url: `/matches/`+ id,
            method: 'delete'
        })
    },

    // 获取选手比赛统计
/*    getPlayerStats(playerId) {
        return request({
            url: `/matches/player/${playerId}/stats`,
            method: 'get'
        })
    },*/

    // 获取选手比赛记录
/*    getPlayerMatches(playerId, page = 1, limit = 10) {
        return request({
            url: `/matches/player/${playerId}/matches`,
            method: 'get',
            params: {
                page,
                size: limit
            }
        })
    }*/
}