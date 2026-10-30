.class Lcom/android/support/Menu$10;
.super Ljava/lang/Object;
.source "Menu.java"

# interfaces
.implements Landroid/view/View$OnClickListener;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/android/support/Menu;->Button(Landroid/widget/LinearLayout;ILjava/lang/String;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/android/support/Menu;

.field final synthetic val$featName:Ljava/lang/String;

.field final synthetic val$featNum:I


# direct methods
.method constructor <init>(Lcom/android/support/Menu;ILjava/lang/String;)V
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

    .line 724
    iput-object p1, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iput p2, p0, Lcom/android/support/Menu$10;->val$featNum:I

    iput-object p3, p0, Lcom/android/support/Menu$10;->val$featName:Ljava/lang/String;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onClick(Landroid/view/View;)V
    .locals 6
    .param p1, "v"    # Landroid/view/View;

    .line 726
    iget v0, p0, Lcom/android/support/Menu$10;->val$featNum:I

    sparse-switch v0, :sswitch_data_0

    goto :goto_0

    .line 729
    :sswitch_0
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    iget-object v1, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v1, v1, Lcom/android/support/Menu;->mSettings:Landroid/widget/LinearLayout;

    invoke-virtual {v0, v1}, Landroid/widget/ScrollView;->removeView(Landroid/view/View;)V

    .line 730
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    iget-object v1, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v1, v1, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v0, v1}, Landroid/widget/ScrollView;->addView(Landroid/view/View;)V

    .line 731
    goto :goto_0

    .line 733
    :sswitch_1
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    const/4 v1, 0x1

    iput-boolean v1, v0, Lcom/android/support/Menu;->stopChecking:Z

    .line 736
    :goto_0
    iget-object v0, p0, Lcom/android/support/Menu$10;->val$featName:Ljava/lang/String;

    iget v1, p0, Lcom/android/support/Menu$10;->val$featNum:I

    const/4 v2, 0x0

    invoke-static {v0, v1, v2}, Lcom/android/support/Preferences;->changeFeatureInt(Ljava/lang/String;II)V

    .line 737
    iget v0, p0, Lcom/android/support/Menu$10;->val$featNum:I

    const/16 v1, 0x13

    if-ne v0, v1, :cond_0

    .line 739
    :try_start_0
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v3, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v3, v3, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    iget-object v4, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v4, v4, Lcom/android/support/Menu;->mTitle:Landroid/widget/TextView;

    iget-object v5, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v5, v5, Lcom/android/support/Menu;->mSubTitle:Landroid/widget/TextView;

    invoke-virtual {v0, v3, v4, v5}, Lcom/android/support/Menu;->Init(Landroid/content/Context;Landroid/widget/TextView;Landroid/widget/TextView;)V

    .line 740
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v0}, Landroid/widget/LinearLayout;->removeAllViews()V

    .line 741
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v3, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    invoke-virtual {v3}, Lcom/android/support/Menu;->GetFeatureList()[Ljava/lang/String;

    move-result-object v3

    iget-object v4, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v4, v4, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-static {v0, v3, v4}, Lcom/android/support/Menu;->access$200(Lcom/android/support/Menu;[Ljava/lang/String;Landroid/widget/LinearLayout;)V

    .line 743
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    invoke-virtual {v0}, Landroid/widget/ScrollView;->removeAllViews()V

    .line 744
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    iget-object v3, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v3, v3, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v0, v3}, Landroid/widget/ScrollView;->addView(Landroid/view/View;)V

    .line 745
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    iget-object v3, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v3, v3, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    invoke-virtual {v3}, Landroid/widget/ScrollView;->getScrollY()I

    move-result v3

    invoke-virtual {v0, v2, v3}, Landroid/widget/ScrollView;->scrollTo(II)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_1

    .line 746
    :catch_0
    move-exception v0

    :goto_1
    nop

    .line 749
    :cond_0
    iget v0, p0, Lcom/android/support/Menu$10;->val$featNum:I

    const/4 v2, 0x7

    if-lt v0, v2, :cond_1

    iget v0, p0, Lcom/android/support/Menu$10;->val$featNum:I

    if-gt v0, v1, :cond_1

    .line 751
    :try_start_1
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v1, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v1, v1, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    iget-object v2, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v2, v2, Lcom/android/support/Menu;->mTitle:Landroid/widget/TextView;

    iget-object v3, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v3, v3, Lcom/android/support/Menu;->mSubTitle:Landroid/widget/TextView;

    invoke-virtual {v0, v1, v2, v3}, Lcom/android/support/Menu;->Init(Landroid/content/Context;Landroid/widget/TextView;Landroid/widget/TextView;)V

    .line 752
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v0, v0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v0}, Landroid/widget/LinearLayout;->removeAllViews()V

    .line 753
    iget-object v0, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v1, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    invoke-virtual {v1}, Lcom/android/support/Menu;->GetFeatureList()[Ljava/lang/String;

    move-result-object v1

    iget-object v2, p0, Lcom/android/support/Menu$10;->this$0:Lcom/android/support/Menu;

    iget-object v2, v2, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-static {v0, v1, v2}, Lcom/android/support/Menu;->access$200(Lcom/android/support/Menu;[Ljava/lang/String;Landroid/widget/LinearLayout;)V
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_1

    .line 755
    goto :goto_2

    .line 754
    :catch_1
    move-exception v0

    .line 757
    :cond_1
    :goto_2
    return-void

    :sswitch_data_0
    .sparse-switch
        -0x64 -> :sswitch_1
        -0x6 -> :sswitch_0
    .end sparse-switch
.end method
