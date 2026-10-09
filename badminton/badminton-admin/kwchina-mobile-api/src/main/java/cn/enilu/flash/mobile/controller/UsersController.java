package cn.enilu.flash.mobile.controller;

import cn.enilu.flash.bean.constant.factory.PageFactory;
import cn.enilu.flash.bean.dto.UserUpdateDTO;
import cn.enilu.flash.bean.entity.system.Users;
import cn.enilu.flash.bean.vo.front.Rets;
import cn.enilu.flash.bean.vo.front.Result;
import cn.enilu.flash.bean.vo.query.SearchFilter;
import cn.enilu.flash.service.system.UsersService;
import cn.enilu.flash.utils.MD5;
import cn.enilu.flash.utils.StringUtil;
import cn.enilu.flash.utils.factory.Page;
import cn.enilu.flash.web.controller.BaseController;
import org.hibernate.type.descriptor.java.DataHelper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


import javax.validation.Valid;
import java.util.List;
//import javax.xml.transform.Result;

@RestController
@RequestMapping("/users")
public class UsersController extends BaseController {

    @Autowired
    private UsersService userService;

    // 获取用户列表（分页+搜索）
    @GetMapping
    public Object list(
            @RequestParam(required = false) String keyword) {
        Page<Users> pageHalper = new PageFactory<Users>().defaultPage();
        if(StringUtil.isNotEmpty(keyword)){
            pageHalper.addFilter(SearchFilter.build("playerName", SearchFilter.Operator.LIKE, keyword));
        }
        pageHalper = userService.queryPage(pageHalper);
        return Rets.success(pageHalper);
    }

    @GetMapping("/referees")
    public Object  getAllReferees() {
        return Rets.success(userService.findAllReferees());
    }

    @GetMapping("/players")
    public Object  getAllPlayers() {
        return Rets.success(userService.findAllPlayers());
    }
    // 创建用户
    @PostMapping
    public Object create(@RequestBody Users user) {
        if(userService.existsByUsername(user.getUserName())) {
            return Rets.failure("用户名已存在");
        }
        userService.save(user);
        return Rets.success();
    }

    // 获取用户详情
    @GetMapping("/{id}")
    public Object get(@PathVariable Long id) {
        return Rets.success(userService.findById(id));
    }

    // 更新用户
    @PutMapping("/{id}")
    public Object update(@PathVariable Long id, @RequestBody Users user) {
        user.setId(id);
        userService.save(user);
        return Rets.success();
    }

    // 删除用户
    @DeleteMapping("/{id}")
    public Object delete(@PathVariable Long id) {
        userService.delete(id);
        return Rets.success();
    }

//    // 获取选手排行榜
//    @GetMapping("/ranking")
//    public Object ranking() {
//        return Rets.success(userService.findAllPlayersOrderByPointsDesc());
//    }

    // 重置密码
    @PostMapping("/{id}/resetPassword")
    public Object resetPassword(@PathVariable Long id) {
        Users user = userService.findById(id).orElse(null);
        if (user == null) {
            return Rets.failure("用户不存在");
        }
        // 重置密码逻辑，实际项目中应加密存储
//        user.setPassword("123456");
        user.setPassword(MD5.md5("User",user.getSalt()));
        userService.save(user);
        return Rets.success();
    }

    @PostMapping("/update")
    public Result updateUser(@RequestBody @Valid UserUpdateDTO userUpdateDTO) {
        try {
            // 直接调用Service层更新
            userService.updateUser(userUpdateDTO);

            // 返回成功结果（假设Result类已存在）
            return Result.success("用户更新成功");

        } catch (IllegalArgumentException e) {
            // 捕获业务校验异常
            return Result.failure(e.getMessage());

        } catch (Exception e) {
            // 捕获其他异常
            return Result.failure("系统错误，更新失败");
        }
    }
}