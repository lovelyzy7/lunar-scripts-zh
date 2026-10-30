.class Lcom/android/support/Menu$20;
.super Ljava/lang/Object;
.source "Menu.java"

# interfaces
.implements Landroid/view/View$OnClickListener;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/android/support/Menu;->addHotSwitchHeader(Landroid/widget/LinearLayout;Z)Landroid/widget/LinearLayout;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/android/support/Menu;

.field final synthetic val$box:Landroid/widget/LinearLayout;

.field final synthetic val$header:Landroid/widget/Button;


# direct methods
.method constructor <init>(Lcom/android/support/Menu;Landroid/widget/LinearLayout;Landroid/widget/Button;)V
    .locals 0
    .param p1, "this$0"    # Lcom/android/support/Menu;
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010,
            0x1010,
            0x1010
        }
        names = {
            null,
            null,
            null
        }
    .end annotation

    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 1259
    iput-object p1, p0, Lcom/android/support/Menu$20;->this$0:Lcom/android/support/Menu;

    iput-object p2, p0, Lcom/android/support/Menu$20;->val$box:Landroid/widget/LinearLayout;

    iput-object p3, p0, Lcom/android/support/Menu$20;->val$header:Landroid/widget/Button;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/view/View;)V
    .locals 4
    .param p1, "v"    # Landroid/view/View;

    .line 1261
    iget-object v0, p0, Lcom/android/support/Menu$20;->val$box:Landroid/widget/LinearLayout;

    invoke-virtual {v0}, Landroid/widget/LinearLayout;->getVisibility()I

    move-result v0

    const/4 v1, 0x0

    if-eqz v0, :cond_0

    const/4 v0, 0x1

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    .line 1262
    .local v0, "nowOpen":Z
    :goto_0
    iget-object v2, p0, Lcom/android/support/Menu$20;->val$box:Landroid/widget/LinearLayout;

    if-eqz v0, :cond_1

    goto :goto_1

    :cond_1
    const/16 v1, 0x8

    :goto_1
    invoke-virtual {v2, v1}, Landroid/widget/LinearLayout;->setVisibility(I)V

    .line 1263
    iget-object v1, p0, Lcom/android/support/Menu$20;->val$header:Landroid/widget/Button;

    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    if-eqz v0, :cond_2

    const-string v3, "\u25be "

    goto :goto_2

    :cond_2
    const-string v3, "\u25b8 "

    :goto_2
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v3, "\u670d\u52a1\u5668\u70ed\u5207\u6362"

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 1264
    :try_start_0
    iget-object v1, p0, Lcom/android/support/Menu$20;->this$0:Lcom/android/support/Menu;

    iget-object v1, v1, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-static {v1}, Lcom/android/support/Preferences;->with(Landroid/content/Context;)Lcom/android/support/Preferences;

    move-result-object v1

    const-string v2, "hotSwitchOpen"

    invoke-virtual {v1, v2, v0}, Lcom/android/support/Preferences;->writeBoolean(Ljava/lang/String;Z)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_3

    :catch_0
    move-exception v1

    .line 1265
    :goto_3
    return-void
.end method
