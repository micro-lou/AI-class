package cn.enilu.flash.service.system;

import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.bean.entity.system.playerData;
import cn.enilu.flash.dao.system.PlayerDataRepository;
import cn.enilu.flash.dao.system.UsersRepository;
import cn.enilu.flash.service.BaseService;
import org.springframework.data.domain.Page;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RankingService extends  BaseService<Users,Long, UsersRepository>   {

    @Autowired
    private UsersRepository usersRepository;

    @Autowired
    private PlayerDataRepository playerDataRepository;

//    public List<Users> findAllPlayersOrderByPointsDesc() {
//        return usersRepository.findByRoleTypeOrderByCurrentPointsDesc(1); // 假设1表示选手
//    }
    public Page<Users> findAllPlayersOrderByPointsDesc(int page, int size) {
    Pageable pageable = PageRequest.of(page, size);
    return usersRepository.findByRoleType(1, pageable); // 假设1表示选手
}

//    public List<Users> searchPlayers(String name) {
//        return usersRepository.findByPlayerName(name);
//    }

    public PlayerStats getPlayerStats(Long id) {
        Users user = usersRepository.findById(id).orElse(null);
        if (user == null) {
            return null;
        }
        playerData data = playerDataRepository.findById(user.getId()).orElse(null);
        if (data == null) {
            return new PlayerStats(user, null);
        }

        return new PlayerStats(user, data);
    }

    public static class PlayerStats {
        private Users user;
        private playerData data;
        private Double singleWinRate;
        private Double doubleWinRate;

        public PlayerStats(Users user, playerData data) {
            this.user = user;
            this.data = data;

            if (data != null) {
                this.singleWinRate = data.getSingleMatches() > 0 ?
                        (double) data.getSingleWin() / data.getSingleMatches() * 100 : 0;
                this.doubleWinRate = data.getDoubleMatches() > 0 ?
                        (double) data.getDoubleWin() / data.getDoubleMatches() * 100 : 0;
            }
        }

        // Getters
        public Users getUser() { return user; }
        public playerData getData() { return data; }
        public Double getSingleWinRate() { return singleWinRate; }
        public Double getDoubleWinRate() { return doubleWinRate; }
    }
}
