package cn.enilu.flash.mobile.controller;

import cn.enilu.flash.bean.constant.factory.PageFactory;
import cn.enilu.flash.bean.entity.system.Matches;
import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.bean.vo.MatchesVo;
import cn.enilu.flash.bean.vo.front.Rets;
import cn.enilu.flash.bean.vo.query.SearchFilter;
import cn.enilu.flash.dao.system.UsersRepository;
import cn.enilu.flash.service.system.MatchesService;
import cn.enilu.flash.service.system.UsersService;
import cn.enilu.flash.utils.StringUtil;
import cn.enilu.flash.utils.factory.Page;
import org.springframework.beans.BeanUtils;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import cn.enilu.flash.web.controller.BaseController;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/matches")
public class MatchesController extends BaseController {

    @Autowired
    private MatchesService matchesService;
    @Autowired
    private UsersRepository usersRepository;



    // 获取比赛列表（分页+搜索）
    @GetMapping("/list")
    public Object list() {
        Page<Matches> page = new PageFactory<Matches>().defaultPage();

     /*   if (StringUtil.isNotEmpty(keyword)) {
            page.addFilter(SearchFilter.build("matchType", SearchFilter.Operator.LIKE, keyword));
        }

        if (StringUtil.isNotEmpty(matchType)) {
            page.addFilter(SearchFilter.build("matchType", SearchFilter.Operator.EQ, matchType));
        }*/
        Sort sort = Sort.by(
                Sort.Order.desc("matchTime")
        );
        page.setSort(sort);
        page = matchesService.queryPage(page);
        List<Matches> list=page.getRecords();
        Page<Matches> result=new Page<>();
        BeanUtils.copyProperties(page,result);
        List<Users>users=usersRepository.findAll();

//        List<MatchesVo> matchesVos=new ArrayList<>();
//        Map<Long,String> userMap=users.stream().collect(Collectors.toMap(Users::getId,Users::getPlayerName));
//        for (Matches matches : list) {
//            MatchesVo matchesVo=new MatchesVo();
//            BeanUtils.copyProperties(matches,matchesVo);
//            if(matches.getRed_1()!=null){
//                matchesVo.setRed1Name(userMap.get(matches.getRed_1()));
//            }
//            if(matches.getRed_2()!=null){
//                matchesVo.setRed2Name(userMap.get(matches.getRed_2()));
//            }
//            if(matches.getBlue_1()!=null){
//                matchesVo.setBlue1Name(userMap.get(matches.getBlue_1()));
//            }
//            if(matches.getBlue_2()!=null){
//                matchesVo.setBlue2Name(userMap.get(matches.getBlue_2()));
//            }
//            matchesVos.add(matchesVo);
//        }
//        result.setRecords(matchesVos);

        return Rets.success(result);
    }

    // 创建比赛
    @PostMapping
    public Object create(@RequestBody Matches match) {
        matchesService.saveMatch(match);
        return Rets.success();
    }

    // 获取比赛详情
    @GetMapping("/{id}")
    public Object get(@PathVariable Integer id) {
        return Rets.success(matchesService.getMatchBymatchId(id));
    }

    // 更新比赛
    @PutMapping("/{id}")
    public Object update(@PathVariable Integer id, @RequestBody Matches match) {
        match.setMatchId(id);
        matchesService.saveMatch(match);
        return Rets.success();
    }

    // 删除比赛
    @DeleteMapping("/{id}")
    public Object delete(@PathVariable Integer id) {
        matchesService.deleteMatch(id);
        return Rets.success();
    }


}