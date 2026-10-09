package cn.enilu.flash.bean.vo.front;

import lombok.Data;

@Data
public class Result {
    private boolean success;
    private String message;
    private int code;

    // 静态工厂方法
    public static Result success(String msg) {
        Result result = new Result();
        result.success = true;
        result.message = msg;
        result.code = 20000;
        return result;
    }

    public static Result failure(String msg) {
        Result result = new Result();
        result.success = false;
        result.message = msg;
        result.code = 400;
        return result;
    }

    // Getter（省略Setter）
    public boolean isSuccess() { return success; }
    public String getMessage() { return message; }
}