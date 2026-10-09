package cn.enilu.flash.service.system;

import cn.enilu.flash.bean.entity.system.Matches;
import cn.enilu.flash.bean.entity.system.ScoreRole;
import cn.enilu.flash.dao.system.MatchesRepository;
import cn.enilu.flash.dao.system.ScoreRoleRepository;
import cn.enilu.flash.service.BaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class ScoreRuleService extends BaseService<ScoreRole, Integer, ScoreRoleRepository> {


    @Autowired
    private ScoreRoleRepository scoreRoleRepository;


    public List<ScoreRole> findAllRules() {
        return scoreRoleRepository.findAll();
    }


}