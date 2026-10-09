package cn.enilu.flash.dao.system;

import cn.enilu.flash.bean.entity.system.Matches;
import cn.enilu.flash.dao.BaseRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;


@Repository
public interface MatchesRepository extends BaseRepository<Matches, Integer> {

   /* @Query("SELECT m FROM Matches m ORDER BY m.matchTime DESC")
    List<Matches> findAllOrderByMatchTimeDesc();

    @Query("SELECT m FROM Matches m WHERE m.red_1 = :id OR m.red_2 = :id OR m.blue_1 = :id OR m.blue_2 = :id ORDER BY m.matchTime DESC")
    List<Matches> findByPlayerId(@Param("userId") Integer id);

    @Query("SELECT m FROM Matches m WHERE m.refereeId = :id ORDER BY m.matchTime DESC")
    List<Matches> findByRefereeId(@Param("userId") Integer id);*/

    Matches findByMatchId(Integer matchId);

    @Query("select  mc from matches mc where mc.isValid = 0 order by mc.recordTime asc")
    List<Matches> findNoResultMatches();

}