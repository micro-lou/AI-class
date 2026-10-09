package cn.enilu.flash.dao.system;

import cn.enilu.flash.bean.entity.system.playerData;
import cn.enilu.flash.bean.entity.system.playerData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;

public interface PlayerDataRepository extends JpaRepository<playerData, Long>, JpaSpecificationExecutor<playerData> {

    // 根据选手ID查找
//    playerData findById(Integer id);

    // 查找单打胜率高于指定值的选手
//    @Query("SELECT p FROM PlayerData p WHERE (p.singleWin*1.0/p.singleMatches) > :winRate")
//    List<PlayerData> findPlayersWithHighSingleWinRate(@Param("winRate") Double winRate);

    // 查找双打胜率高于指定值的选手
//    @Query("SELECT p FROM PlayerData p WHERE (p.doubleWin*1.0/p.doubleMatches) > :winRate")
//    List<PlayerData> findPlayersWithHighDoubleWinRate(@Param("winRate") Double winRate);

    // 更新单打数据
   /* @Query("UPDATE PlayerData p SET p.totalSscore = p.totalSscore + :score, " +
            "p.singleMatches = p.singleMatches + 1, " +
            "p.singleWin = p.singleWin + :win WHERE p.playerId = :playerId")
    void updateSingleMatchStats(@Param("playerId") Integer playerId,
                                @Param("score") Integer score,
                                @Param("win") Integer win);*/

}