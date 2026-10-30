.class Lcom/android/support/Menu$6;
.super Ljava/lang/Object;
.source "Menu.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/android/support/Menu;->ShowMenu()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/android/support/Menu;

.field final synthetic val$handler:Landroid/os/Handler;

.field viewLoaded:Z

.field waitTicks:I


# direct methods
.method constructor <init>(Lcom/android/support/Menu;Landroid/os/Handler;)V
    .locals 0
    .param p1, "this$0"    # Lcom/android/support/Menu;
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010,
            0x1010
        }
        names = {
            null,
            null
        }
    .end annotation

    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 382
    iput-object p1, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iput-object p2, p0, Lcom/android/support/Menu$6;->val$handler:Landroid/os/Handler;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 383
    const/4 p2, 0x0

    iput-boolean p2, p0, Lcom/android/support/Menu$6;->viewLoaded:Z

    .line 384
    iput p2, p0, Lcom/android/support/Menu$6;->waitTicks:I

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 391
    sget-boolean v0, Lcom/android/support/Preferences;->loadPref:Z

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    invoke-virtual {v0}, Lcom/android/support/Menu;->IsGameLibLoaded()Z

    move-result v0

    if-nez v0, :cond_1

    iget-object v0, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-boolean v0, v0, Lcom/android/support/Menu;->stopChecking:Z

    if-nez v0, :cond_1

    .line 392
    iget-boolean v0, p0, Lcom/android/support/Menu$6;->viewLoaded:Z

    const/4 v1, 0x1

    if-nez v0, :cond_0

    iget v0, p0, Lcom/android/support/Menu$6;->waitTicks:I

    const/16 v2, 0x10

    if-lt v0, v2, :cond_0

    .line 393
    iget-object v0, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v2, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v2, v2, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    const-string v3, "\u5df2\u5f00\u542f\u300c\u4fdd\u5b58\u529f\u80fd\u504f\u597d\u300d\uff1a\u6b63\u5728\u7b49\u5f85\u6e38\u620f\u5e93\u52a0\u8f7d\u2026\u2026\n\n\u4e5f\u53ef\u70b9\u4e0b\u65b9\u6309\u94ae\u5f3a\u5236\u52a0\u8f7d\uff08\u90e8\u5206\u529f\u80fd\u53ef\u80fd\u9700\u8981\u91cd\u65b0\u6fc0\u6d3b\u4e00\u6b21\uff09"

    invoke-static {v0, v2, v3}, Lcom/android/support/Menu;->access$000(Lcom/android/support/Menu;Landroid/widget/LinearLayout;Ljava/lang/String;)V

    .line 394
    iget-object v0, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v2, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v2, v2, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    const/16 v3, -0x64

    const-string v4, "\u5f3a\u5236\u52a0\u8f7d\u83dc\u5355"

    invoke-static {v0, v2, v3, v4}, Lcom/android/support/Menu;->access$100(Lcom/android/support/Menu;Landroid/widget/LinearLayout;ILjava/lang/String;)V

    .line 395
    iput-boolean v1, p0, Lcom/android/support/Menu$6;->viewLoaded:Z

    .line 397
    :cond_0
    iget v0, p0, Lcom/android/support/Menu$6;->waitTicks:I

    add-int/2addr v0, v1

    iput v0, p0, Lcom/android/support/Menu$6;->waitTicks:I

    .line 398
    iget-object v0, p0, Lcom/android/support/Menu$6;->val$handler:Landroid/os/Handler;

    const-wide/16 v1, 0x258

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 400
    :cond_1
    iget-object v0, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v0}, Landroid/widget/LinearLayout;->removeAllViews()V

    .line 401
    iget-object v0, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v1, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    invoke-virtual {v1}, Lcom/android/support/Menu;->GetFeatureList()[Ljava/lang/String;

    move-result-object v1

    iget-object v2, p0, Lcom/android/support/Menu$6;->this$0:Lcom/android/support/Menu;

    iget-object v2, v2, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-static {v0, v1, v2}, Lcom/android/support/Menu;->access$200(Lcom/android/support/Menu;[Ljava/lang/String;Landroid/widget/LinearLayout;)V

    .line 403
    :goto_0
    return-void
.end method
