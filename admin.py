from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

admin = Admin(name="독약한방")


class HerbView(ModelView):
    # can_delete = False
    can_view_details = True
    # create_modal = True
    form_columns = ['herb_id', 'group_id_fk', 'category_id_fk',
                    'herb_name', 'major_effect', 'effect', 'origin', 'scientific_name', 'is_poison', 'figure_feature',
                    'image_path']


class SimilarityGroupView(ModelView):
    can_view_details = True
    form_columns = ['group_id',
                    'group_name']


class CategoryView(ModelView):
    can_view_details = True
    form_columns = ['category_id',
                    'category_name']


class LocationView(ModelView):
    can_view_details = True
    form_columns = ['location_id', 'herb_id_fk',
                    'country', 'location_name', 'pos_x', 'pos_y']


class NewsView(ModelView):
    can_view_details = True
    form_columns = ['news_id', 'herb_id_fk',
                    'title', 'date', 'url']


class JournalView(ModelView):
    can_view_details = True
    form_columns = ['journal_id', 'herb_id_fk',
                    'title', 'date', 'url']
