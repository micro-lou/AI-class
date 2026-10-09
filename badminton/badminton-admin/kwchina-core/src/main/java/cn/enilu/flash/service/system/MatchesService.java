package cn.enilu.flash.service.system;

import cn.enilu.flash.bean.entity.system.Matches;
import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.dao.system.MatchesRepository;
import cn.enilu.flash.dao.system.UsersRepository;
import cn.enilu.flash.service.BaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class MatchesService extends BaseService<Matches,Integer, MatchesRepository> {

    @Autowired
    private MatchesRepository matchesRepository;

   /* public List<Matches> getAllMatches() {
        return matchesRepository.findAllOrderByMatchTimeDesc();
    }*/

    public Matches getMatchBymatchId(Integer matchId) {
        return matchesRepository.findByMatchId(matchId);
    }

    public Matches saveMatch(Matches match) {
        return matchesRepository.save(match);
    }

    public void deleteMatch(Integer matchId) {
        matchesRepository.deleteById(matchId);
    }

    public List<Matches> getMatchesByPlayer(Integer id) {
        return new ArrayList<>();
//        return matchesRepository.findByPlayerId(id);
    }


    public List<Matches> findNoResultMatches(){
        return matchesRepository.findNoResultMatches();

    }


    public List<Matches> getMatchesByReferee(Integer id) {
        return new ArrayList<>();
//        return matchesRepository.findByRefereeId(id);
    }
    public Matches save(Matches match) {
        return matchesRepository.save(match);
    }
}