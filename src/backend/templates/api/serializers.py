from rest_framework import serializers

from templates.models import Template, Purpose, TemplatePurpose


class TemplateRenderTestmailRequestSerializer(serializers.Serializer):
    counselor = serializers.IntegerField(help_text="Counselor ID")


class TemplateSerializer(serializers.ModelSerializer):
    purposes = serializers.ListField(
        child=serializers.ChoiceField(choices=Purpose.choices),
        required=False,
    )

    class Meta:
        model = Template
        fields = ["id", "name", "content", "purposes", "created_at", "updated_at"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["purposes"] = list(instance.template_purposes.values_list("purpose", flat=True))
        return rep

    def create(self, validated_data):
        purposes = validated_data.pop("purposes", [])
        template = Template.objects.create(**validated_data)
        self._sync_purposes(template, purposes)
        return template

    def update(self, instance, validated_data):
        purposes = validated_data.pop("purposes", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if purposes is not None:
            self._sync_purposes(instance, purposes)
        return instance

    def _sync_purposes(self, template, purposes):
        new_set = set(purposes)
        existing_set = set(template.template_purposes.values_list("purpose", flat=True))
        template.template_purposes.filter(purpose__in=existing_set - new_set).delete()
        TemplatePurpose.objects.bulk_create([
            TemplatePurpose(template=template, purpose=p)
            for p in new_set - existing_set
        ])