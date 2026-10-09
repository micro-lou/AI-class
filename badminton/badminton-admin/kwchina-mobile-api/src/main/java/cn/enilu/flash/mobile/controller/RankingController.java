// RankingController.java
package cn.enilu.flash.mobile.controller;

import cn.enilu.flash.bean.constant.factory.PageFactory;
import cn.enilu.flash.bean.core.BussinessLog;
import cn.enilu.flash.bean.entity.system.Matches;
import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.bean.vo.MatchesVo;
import cn.enilu.flash.bean.vo.front.Rets;
import cn.enilu.flash.bean.vo.query.SearchFilter;
import cn.enilu.flash.service.system.MatchesService;
import cn.enilu.flash.service.system.RankingService;
import cn.enilu.flash.utils.factory.Page;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;


@RestController
@RequestMapping("/ranking")
public class RankingController {

    @Autowired
    private RankingService rankingService;

    @Autowired
    private MatchesService matchesService;

    //    @GetMapping("/list")
//    public List<Users> getRankingList() {
//        return rankingService.findAllPlayersOrderByPointsDesc();
//    }
    @GetMapping("/list")
    public Object getRankingList() {
        Page<Users> pageHalper = new PageFactory<Users>().defaultPage();
        pageHalper.addFilter(SearchFilter.build("roleType", SearchFilter.Operator.EQ, 1));
        Sort sort = Sort.by(
                Sort.Order.desc("currentPoints")
        );
        pageHalper.setSort(sort);
        pageHalper = rankingService.queryPage(pageHalper);
        return Rets.success(pageHalper);
//    return rankingService.findAllPlayersOrderByPointsDesc(page, size);
    }
//    @GetMapping("/search")
//    public List<Users> searchPlayers(@RequestParam String name) {
//        return rankingService.searchPlayers(name);
//    }

    @GetMapping("/player/{id}")
    @BussinessLog(value = "查看选手详情", key = "id")
    public Object getPlayerStats(@PathVariable Long id) {

        return Rets.success(rankingService.getPlayerStats(id));
    }

    @PostMapping("/matches")
    public Object create(@RequestBody MatchesVo matchesVo) {
        Matches matches = new Matches();
        BeanUtils.copyProperties(matchesVo, matches);
        matches.setIsValid(0);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        LocalDateTime matchTime = LocalDateTime.parse(matchesVo.getMatchTime() + ":00", formatter);
        matches.setMatchTime(matchTime);
        matches.setRecordTime(LocalDateTime.now());
        if (matches.getBluePoints() < matches.getRedPoints()) {
            matches.setWinner("red");
        } else {
            matches.setWinner("blue");
        }
        matchesService.save(matches);
        return Rets.success();
    }

//    @GetMapping
//    @RequiresPermissions(value = {Permission.MATCHES_VIEW})
//    public Object list() {
//        return Rets.success( matchesService.getAllMatches());
//    }
}